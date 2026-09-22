from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from . import __version__
from .generator import generate_resume
from .models import EducationEntry, ResumeData, SkillEntry
from .validator import validate_resume


APP_BG = "#F4F7FB"
WHITE = "#FFFFFF"
INK = "#172033"
MUTED = "#6F7E94"
LINE = "#DFE6F1"
BLUE = "#246BDE"
BLUE_DARK = "#174DA8"
BLUE_SOFT = "#EDF4FF"


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, style="Content.TFrame")
        self.canvas = tk.Canvas(
            self,
            background=WHITE,
            highlightthickness=0,
            borderwidth=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.content = ttk.Frame(self.canvas, style="Content.TFrame")
        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw",
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.content.bind("<MouseWheel>", self._on_mousewheel)

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> str:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")
        return "break"


class ResumeGeneratorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("简历生成器")
        self.root.geometry("1080x840")
        self.root.minsize(900, 700)
        self.root.configure(background=APP_BG)
        self._center_window()

        self.photo_path = tk.StringVar()
        self.output_dir = tk.StringVar(
            value=str((Path.home() / "Documents" / "ResumeOutput").resolve())
        )
        self.filename = tk.StringVar(value="个人简历")
        self.status = tk.StringVar(value="填写信息后即可生成 PNG 与 PDF")
        self.result_files = None
        self.photo_preview: ImageTk.PhotoImage | None = None

        self.vars: dict[str, tk.StringVar] = {}
        self.education_vars: list[dict[str, tk.StringVar]] = []
        self.skill_vars: list[dict[str, tk.StringVar]] = []

        self._configure_styles()
        self._build_layout()
        self._bind_shortcuts()

    def _center_window(self) -> None:
        self.root.update_idletasks()
        width = 1080
        height = 840
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("TFrame", background=WHITE)
        style.configure("App.TFrame", background=APP_BG)
        style.configure("Content.TFrame", background=WHITE)
        style.configure("Header.TFrame", background=WHITE)
        style.configure("Footer.TFrame", background=WHITE)
        style.configure(
            "Title.TLabel",
            background=WHITE,
            foreground=INK,
            font=("Microsoft YaHei UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=WHITE,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Eyebrow.TLabel",
            background=WHITE,
            foreground=BLUE,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.configure(
            "Field.TLabel",
            background=WHITE,
            foreground=INK,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.configure(
            "Hint.TLabel",
            background=WHITE,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=WHITE,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "TEntry",
            padding=(9, 7),
            fieldbackground=WHITE,
            bordercolor=LINE,
            lightcolor=LINE,
            darkcolor=LINE,
            font=("Microsoft YaHei UI", 10),
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", BLUE)],
            lightcolor=[("focus", BLUE)],
            darkcolor=[("focus", BLUE)],
        )
        style.configure(
            "TSpinbox",
            padding=(8, 6),
            fieldbackground=WHITE,
            bordercolor=LINE,
            arrowsize=14,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "TNotebook",
            background=WHITE,
            borderwidth=0,
            tabmargins=(24, 10, 24, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background="#F6F8FC",
            foreground=MUTED,
            borderwidth=0,
            padding=(17, 10),
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BLUE_SOFT), ("active", "#F0F5FD")],
            foreground=[("selected", BLUE_DARK), ("active", INK)],
        )
        style.configure(
            "TLabelframe",
            background=WHITE,
            bordercolor=LINE,
            lightcolor=LINE,
            darkcolor=LINE,
            padding=16,
        )
        style.configure(
            "TLabelframe.Label",
            background=WHITE,
            foreground=BLUE_DARK,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.configure(
            "Primary.TButton",
            background=BLUE,
            foreground=WHITE,
            borderwidth=0,
            padding=(20, 11),
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", BLUE_DARK), ("disabled", "#AFC1DD")],
            foreground=[("disabled", WHITE)],
        )
        style.configure(
            "Secondary.TButton",
            background="#F5F8FD",
            foreground=BLUE_DARK,
            bordercolor="#CFE0FA",
            lightcolor="#CFE0FA",
            darkcolor="#CFE0FA",
            padding=(14, 9),
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", BLUE_SOFT), ("disabled", "#F4F6F8")],
            foreground=[("disabled", "#A5AFC0")],
        )
        style.configure(
            "TScrollbar",
            background="#E8EEF7",
            troughcolor=WHITE,
            bordercolor=WHITE,
            arrowcolor=MUTED,
        )

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=(22, 18, 22, 18))
        outer.pack(fill="both", expand=True)

        shell = ttk.Frame(outer, style="Header.TFrame")
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(shell, style="Header.TFrame", padding=(24, 19, 24, 13))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_group = ttk.Frame(header, style="Header.TFrame")
        title_group.grid(row=0, column=0, sticky="w")
        ttk.Label(
            title_group,
            text="RESUME STUDIO",
            style="Eyebrow.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            title_group,
            text="简历生成器",
            style="Title.TLabel",
        ).pack(anchor="w", pady=(1, 2))
        ttk.Label(
            title_group,
            text="填写信息，一键输出高清 PNG 与打印级 PDF",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        version_label = ttk.Label(
            header,
            text=f"v{__version__}  ·  本地处理",
            style="Hint.TLabel",
        )
        version_label.grid(row=0, column=1, sticky="e")

        ttk.Separator(shell).grid(row=0, column=0, sticky="sew")

        self.notebook = ttk.Notebook(shell)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self._build_basic_tab()
        self._build_education_tab()
        self._build_skills_tab()
        self._build_contact_tab()
        self._build_export_tab()

        footer = ttk.Frame(
            shell,
            style="Footer.TFrame",
            padding=(24, 12, 24, 8),
        )
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ttk.Separator(footer).grid(row=0, column=0, columnspan=3, sticky="new")
        ttk.Label(
            footer,
            textvariable=self.status,
            style="Status.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))

        self.open_button = ttk.Button(
            footer,
            text="打开输出目录",
            style="Secondary.TButton",
            command=self._open_output_directory,
            state="disabled",
        )
        self.open_button.grid(row=1, column=1, padx=(12, 8), pady=(12, 0))

        self.generate_button = ttk.Button(
            footer,
            text="生成简历",
            style="Primary.TButton",
            command=self._generate,
        )
        self.generate_button.grid(row=1, column=2, pady=(12, 0))

    def _new_scroll_tab(self, title: str) -> ScrollableFrame:
        tab = ScrollableFrame(self.notebook)
        self.notebook.add(tab, text=title)
        return tab

    def _var(self, name: str) -> tk.StringVar:
        variable = tk.StringVar()
        self.vars[name] = variable
        return variable

    def _add_entry(
        self,
        parent: ttk.Frame,
        row: int,
        column: int,
        label: str,
        variable: tk.StringVar,
        hint: str = "",
        *,
        columnspan: int = 1,
    ) -> ttk.Entry:
        field = ttk.Frame(parent, style="Content.TFrame")
        field.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=(0, 20) if column == 0 else (20, 0),
            pady=(0, 17),
        )
        field.grid_columnconfigure(0, weight=1)
        ttk.Label(field, text=label, style="Field.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6),
        )
        entry = ttk.Entry(field, textvariable=variable)
        entry.grid(row=1, column=0, sticky="ew")
        if hint:
            ttk.Label(field, text=hint, style="Hint.TLabel").grid(
                row=2,
                column=0,
                sticky="w",
                pady=(4, 0),
            )
        return entry

    def _build_basic_tab(self) -> None:
        tab = self._new_scroll_tab("基本信息")
        content = tab.content
        content.grid_columnconfigure(0, weight=1)

        photo_frame = ttk.LabelFrame(content, text="头像")
        photo_frame.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 12))
        photo_frame.grid_columnconfigure(1, weight=1)

        self.photo_label = tk.Label(
            photo_frame,
            text="照片\n预览",
            width=10,
            height=5,
            background="#F6F9FF",
            foreground=MUTED,
            font=("Microsoft YaHei UI", 9),
            compound="center",
        )
        self.photo_label.grid(row=0, column=0, rowspan=2, padx=(0, 16), sticky="w")

        ttk.Label(
            photo_frame,
            text="选择一张清晰的正方形照片，生成时会自动裁剪为圆形。",
            style="Hint.TLabel",
        ).grid(row=0, column=1, sticky="w")
        photo_actions = ttk.Frame(photo_frame, style="Content.TFrame")
        photo_actions.grid(row=1, column=1, sticky="w", pady=(10, 0))
        ttk.Button(
            photo_actions,
            text="选择照片",
            style="Secondary.TButton",
            command=self._choose_photo,
        ).pack(side="left")
        ttk.Button(
            photo_actions,
            text="移除",
            style="Secondary.TButton",
            command=self._clear_photo,
        ).pack(side="left", padx=(8, 0))

        form = ttk.LabelFrame(content, text="个人信息")
        form.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        self._add_entry(form, 0, 0, "姓名 *", self._var("name"), "必填，最多 24 个字符")
        self._add_entry(
            form,
            0,
            1,
            "求职意向 *",
            self._var("job_target"),
            "例如：产品经理 / UI 设计师",
        )
        self._add_entry(form, 1, 0, "所在城市", self._var("city"), "例如：上海")
        self._add_entry(form, 1, 1, "工作年限", self._var("work_years"), "例如：5 年")
        self._add_entry(form, 2, 0, "到岗时间", self._var("availability"), "例如：一周内")
        self._add_entry(form, 2, 1, "出生年月", self._var("birth_date"), "例如：1998.06")
        self._add_entry(
            form,
            3,
            0,
            "政治面貌",
            self._var("political_status"),
            "例如：中共党员",
        )
        self._add_entry(
            form,
            3,
            1,
            "最高学历",
            self._var("highest_education"),
            "例如：本科",
        )
        self._add_entry(
            form,
            4,
            0,
            "现居地址",
            self._var("current_address"),
            "用于基本信息模块",
            columnspan=2,
        )

    def _build_education_tab(self) -> None:
        tab = self._new_scroll_tab("教育背景")
        content = tab.content
        content.grid_columnconfigure(0, weight=1)

        for index in range(2):
            variables = {
                "school": tk.StringVar(),
                "date_range": tk.StringVar(),
                "major": tk.StringVar(),
                "details": tk.StringVar(),
            }
            self.education_vars.append(variables)
            frame = ttk.LabelFrame(
                content,
                text=f"教育经历 {index + 1}" + (" *" if index == 0 else "（可选）"),
            )
            frame.grid(
                row=index,
                column=0,
                sticky="ew",
                padx=22,
                pady=(18 if index == 0 else 0, 18),
            )
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=1)
            self._add_entry(
                frame,
                0,
                0,
                "学校名称",
                variables["school"],
                "至少填写第一段教育经历",
            )
            self._add_entry(
                frame,
                0,
                1,
                "起止时间",
                variables["date_range"],
                "例如：2020.09 - 2024.06",
            )
            self._add_entry(
                frame,
                1,
                0,
                "专业 / 学历",
                variables["major"],
                "例如：计算机科学 / 本科",
            )
            self._add_entry(
                frame,
                1,
                1,
                "补充说明",
                variables["details"],
                "主修课程、荣誉奖项或校园经历，建议 90 字内",
            )

    def _build_skills_tab(self) -> None:
        tab = self._new_scroll_tab("技能特长")
        content = tab.content
        content.grid_columnconfigure(0, weight=1)

        skills_frame = ttk.LabelFrame(content, text="核心技能")
        skills_frame.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 12))
        for column in range(4):
            skills_frame.grid_columnconfigure(column, weight=1)

        for index in range(4):
            variables = {
                "name": tk.StringVar(),
                "level": tk.StringVar(value="熟练" if index < 2 else "掌握"),
                "score": tk.StringVar(value=str([92, 85, 78, 68][index])),
            }
            self.skill_vars.append(variables)
            row = (index // 2) * 3
            column = (index % 2) * 2
            field = ttk.Frame(skills_frame, style="Content.TFrame")
            field.grid(
                row=row,
                column=column,
                columnspan=2,
                sticky="ew",
                padx=(0, 18) if index % 2 == 0 else (18, 0),
                pady=(0, 12),
            )
            field.grid_columnconfigure(0, weight=1)
            ttk.Label(
                field,
                text=f"技能 {index + 1}",
                style="Field.TLabel",
            ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
            ttk.Entry(field, textvariable=variables["name"]).grid(
                row=1,
                column=0,
                sticky="ew",
                padx=(0, 8),
            )
            ttk.Entry(field, textvariable=variables["level"], width=9).grid(
                row=1,
                column=1,
                sticky="ew",
                padx=(0, 8),
            )
            ttk.Spinbox(
                field,
                from_=0,
                to=100,
                textvariable=variables["score"],
                width=6,
            ).grid(row=1, column=2, sticky="ew")
            ttk.Label(
                field,
                text="技能名称 · 熟练度 · 评分",
                style="Hint.TLabel",
            ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        tags_frame = ttk.LabelFrame(content, text="其他标签")
        tags_frame.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))
        tags_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(
            tags_frame,
            text="使用中文逗号或英文逗号分隔，例如：Photoshop, Figma, 英语 CET-6",
            style="Hint.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 7))
        ttk.Entry(tags_frame, textvariable=self._var("skill_tags")).grid(
            row=1,
            column=0,
            sticky="ew",
        )

    def _build_contact_tab(self) -> None:
        tab = self._new_scroll_tab("联系方式")
        content = tab.content
        content.grid_columnconfigure(0, weight=1)

        contacts = ttk.LabelFrame(content, text="联系信息")
        contacts.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 12))
        contacts.grid_columnconfigure(0, weight=1)
        contacts.grid_columnconfigure(1, weight=1)
        self._add_entry(
            contacts,
            0,
            0,
            "手机号码",
            self._var("phone"),
            "支持数字、空格、连字符和 +86",
        )
        self._add_entry(
            contacts,
            0,
            1,
            "电子邮箱",
            self._var("email"),
            "例如：name@example.com",
        )
        self._add_entry(
            contacts,
            1,
            0,
            "个人网站 / 作品集",
            self._var("portfolio"),
            "可填写网址或作品集地址",
        )
        self._add_entry(
            contacts,
            1,
            1,
            "通讯地址",
            self._var("contact_address"),
            "建议只填写城市或区域",
        )

        evaluation_frame = ttk.LabelFrame(content, text="他人评价 / 自荐语")
        evaluation_frame.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))
        evaluation_frame.grid_columnconfigure(0, weight=1)
        ttk.Label(
            evaluation_frame,
            text="建议 180 字以内，内容会显示在联系方式模块下方。",
            style="Hint.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 7))
        self.evaluation_text = tk.Text(
            evaluation_frame,
            height=7,
            wrap="word",
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=LINE,
            highlightcolor=BLUE,
            background=WHITE,
            foreground=INK,
            insertbackground=BLUE,
            font=("Microsoft YaHei UI", 10),
            padx=10,
            pady=9,
        )
        self.evaluation_text.grid(row=1, column=0, sticky="ew")

    def _build_export_tab(self) -> None:
        tab = self._new_scroll_tab("导出设置")
        content = tab.content
        content.grid_columnconfigure(0, weight=1)

        export_frame = ttk.LabelFrame(content, text="输出文件")
        export_frame.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 12))
        export_frame.grid_columnconfigure(0, weight=1)

        self._add_entry(
            export_frame,
            0,
            0,
            "文件名",
            self.filename,
            "最终会生成“文件名.png”和“文件名.pdf”",
            columnspan=2,
        )

        directory_field = ttk.Frame(export_frame, style="Content.TFrame")
        directory_field.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        directory_field.grid_columnconfigure(0, weight=1)
        ttk.Label(
            directory_field,
            text="输出目录",
            style="Field.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        ttk.Entry(directory_field, textvariable=self.output_dir).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        ttk.Button(
            directory_field,
            text="选择目录",
            style="Secondary.TButton",
            command=self._choose_output_dir,
        ).grid(row=1, column=1)

        note = tk.Label(
            export_frame,
            text=(
                "输出规格\n"
                "PNG：2480 × 3508 像素，300 DPI，适合直接发送或打印\n"
                "PDF：标准 A4 单页，内容与 PNG 完全一致"
            ),
            justify="left",
            anchor="w",
            background="#F7FAFF",
            foreground=INK,
            padx=16,
            pady=14,
            font=("Microsoft YaHei UI", 10),
        )
        note.grid(row=2, column=0, columnspan=2, sticky="ew")

        privacy = tk.Label(
            content,
            text="隐私说明：所有资料只在本机处理，不会上传到任何服务器。",
            justify="left",
            anchor="w",
            background=WHITE,
            foreground=MUTED,
            font=("Microsoft YaHei UI", 9),
        )
        privacy.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 18))

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-Return>", lambda _event: self._generate())
        self.root.bind("<Control-o>", lambda _event: self._choose_photo())

    def _choose_photo(self) -> None:
        path = filedialog.askopenfilename(
            title="选择头像",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self.photo_path.set(path)
        self._update_photo_preview(path)

    def _clear_photo(self) -> None:
        self.photo_path.set("")
        self.photo_preview = None
        self.photo_label.configure(image="", text="照片\n预览")

    def _update_photo_preview(self, path: str) -> None:
        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail((104, 104), Image.Resampling.LANCZOS)
            self.photo_preview = ImageTk.PhotoImage(image)
            self.photo_label.configure(image=self.photo_preview, text="")
        except (OSError, ValueError):
            self._clear_photo()
            messagebox.showerror("无法读取图片", "请选择有效的 JPG、PNG、WEBP 或 BMP 图片。")

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.output_dir.get() or str(Path.home()),
        )
        if path:
            self.output_dir.set(path)

    def _split_tags(self, value: str) -> list[str]:
        return [
            tag.strip()
            for tag in value.replace("，", ",").split(",")
            if tag.strip()
        ]

    def _collect_data(self) -> ResumeData:
        educations = [
            EducationEntry(
                school=variables["school"].get().strip(),
                date_range=variables["date_range"].get().strip(),
                major=variables["major"].get().strip(),
                details=variables["details"].get().strip(),
            )
            for variables in self.education_vars
        ]
        skills: list[SkillEntry] = []
        for variables in self.skill_vars:
            try:
                score = int(variables["score"].get().strip())
            except ValueError:
                score = -1
            skills.append(
                SkillEntry(
                    name=variables["name"].get().strip(),
                    level=variables["level"].get().strip(),
                    score=score,
                )
            )

        return ResumeData(
            name=self.vars["name"].get().strip(),
            job_target=self.vars["job_target"].get().strip(),
            city=self.vars["city"].get().strip(),
            work_years=self.vars["work_years"].get().strip(),
            availability=self.vars["availability"].get().strip(),
            birth_date=self.vars["birth_date"].get().strip(),
            political_status=self.vars["political_status"].get().strip(),
            highest_education=self.vars["highest_education"].get().strip(),
            current_address=self.vars["current_address"].get().strip(),
            educations=educations,
            skills=skills,
            skill_tags=self._split_tags(self.vars["skill_tags"].get()),
            phone=self.vars["phone"].get().strip(),
            email=self.vars["email"].get().strip(),
            portfolio=self.vars["portfolio"].get().strip(),
            contact_address=self.vars["contact_address"].get().strip(),
            evaluation=self.evaluation_text.get("1.0", "end-1c").strip(),
            photo_path=self.photo_path.get().strip(),
        )

    def _generate(self) -> None:
        data = self._collect_data()
        result = validate_resume(data, self.output_dir.get())

        if not result.is_valid:
            messagebox.showerror(
                "请检查填写内容",
                "\n".join(f"• {error}" for error in result.errors),
            )
            self.status.set("校验未通过，请修正页面中的提示内容")
            return

        if result.warnings:
            proceed = messagebox.askyesno(
                "信息提示",
                "\n".join(f"• {warning}" for warning in result.warnings)
                + "\n\n是否继续生成？",
            )
            if not proceed:
                return

        self.generate_button.configure(state="disabled")
        self.status.set("正在生成高清简历，请稍候…")
        self.root.update_idletasks()

        try:
            generated = generate_resume(
                data,
                self.output_dir.get(),
                self.filename.get(),
            )
        except Exception as exc:
            messagebox.showerror("生成失败", str(exc))
            self.status.set("生成失败，请检查填写内容和输出目录")
            return
        finally:
            self.generate_button.configure(state="normal")

        self.result_files = generated
        self.open_button.configure(state="normal")
        self.status.set(f"已生成：{generated.image_path.name} 与 {generated.pdf_path.name}")
        messagebox.showinfo(
            "生成完成",
            "PNG 与 PDF 已生成：\n\n"
            f"{generated.image_path}\n"
            f"{generated.pdf_path}",
        )

    def _open_output_directory(self) -> None:
        if not self.result_files:
            return
        directory = self.result_files.pdf_path.parent
        try:
            if sys.platform == "win32":
                os.startfile(directory)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(directory)])
            else:
                subprocess.Popen(["xdg-open", str(directory)])
        except OSError as exc:
            messagebox.showerror("无法打开目录", str(exc))


def main() -> None:
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass

    root = tk.Tk()
    ResumeGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
