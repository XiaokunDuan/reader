#!/usr/bin/env python3
"""
Knowledge Tool — 智能归类 & 图表生成
"""
import sys
import io
import os
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path

import yaml
from PIL import Image
import customtkinter as ctk
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))
from modules.ai_adapter import create_ai_adapter
from modules.knowledge import KnowledgeAnalyzer
from modules.obsidian import ObsidianWriter


# ── Design tokens ────────────────────────────────────────────────────────────

ACCENT       = "#5B6EF5"
ACCENT_HOVER = "#4857E8"
SUCCESS      = "#16a34a"
ERROR        = "#dc2626"
WARN         = "#d97706"

BORDER    = ("gray82", "gray30")
CARD_BG   = ("gray95", "gray17")
INPUT_BG  = ("white",  "gray13")
TOPBAR_BG = ("gray97", "gray14")
STATUS_BG = ("gray93", "gray16")
SUBTLE    = ("gray52", "gray58")


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    with open(Path(__file__).parent / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


TEMP_PNG       = "/tmp/knowledge_viz.png"
PLAYLIST_CACHE = Path(__file__).parent / "data" / "last_playlist.json"


def extract_python_code(text: str) -> str | None:
    """从 AI 响应中提取 Python 代码块"""
    if "```python" in text:
        return text.split("```python")[1].split("```")[0].strip()
    if "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    if text.strip().startswith("import"):
        return text.strip()
    return None


def run_matplotlib_code(py_code: str) -> tuple[bytes | None, str]:
    """
    执行 matplotlib Python 代码，返回 (PNG bytes, error_msg)。
    代码需自行将图保存到 TEMP_PNG。
    """
    # 确保代码保存到指定路径
    code = py_code.replace("plt.show()", "")
    if TEMP_PNG not in code:
        # 替换任何 savefig 路径，或追加 savefig
        import re
        code = re.sub(r"plt\.savefig\(['\"][^'\"]+['\"]", f"plt.savefig('{TEMP_PNG}'", code)
        if "savefig" not in code:
            code += f"\nplt.savefig('{TEMP_PNG}', dpi=150, bbox_inches='tight', facecolor='white')\nplt.close()"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        script = f.name

    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and os.path.exists(TEMP_PNG):
            data = Path(TEMP_PNG).read_bytes()
            return data, ""
        err = (result.stderr or result.stdout or "未知错误").strip()[-300:]
        return None, err
    except subprocess.TimeoutExpired:
        return None, "执行超时（>30s）"
    except Exception as e:
        return None, str(e)
    finally:
        os.unlink(script)


# ── App ──────────────────────────────────────────────────────────────────────

class KnowledgeTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Fonts — must be created after root window exists
        self.F_LABEL = ctk.CTkFont(size=12)
        self.F_BODY  = ctk.CTkFont(size=13)
        self.F_MONO  = ctk.CTkFont(family="Menlo", size=12)
        self.F_TITLE = ctk.CTkFont(size=14, weight="bold")
        self.F_BTN   = ctk.CTkFont(size=13)

        cfg = load_config()
        self.config   = cfg
        self.ai       = create_ai_adapter(cfg)
        self.obsidian = ObsidianWriter(cfg)
        self.analyzer = KnowledgeAnalyzer(cfg, self.obsidian.scan_vault_structure())

        self._classify_result: dict | None = None
        self._py_code:         str  | None = None   # matplotlib 代码
        self._diagram_png:     bytes| None = None
        self._ctk_image = None  # GC guard

        self._setup_window()
        self._build_ui()

    # ── Window ───────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.title("Knowledge Tool")
        self.geometry("480x700")
        self.minsize(440, 580)

    # ── Top-level layout ─────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        topbar = ctk.CTkFrame(self, fg_color=TOPBAR_BG, height=52, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        ctk.CTkLabel(topbar, text="Knowledge Tool", font=self.F_TITLE).pack(side="left", padx=18)

        self._seg = ctk.CTkSegmentedButton(
            topbar, values=["归类", "图表", "课程"],
            command=self._switch_page,
            font=self.F_BTN, width=216, height=28, corner_radius=7,
            fg_color=("gray86", "gray24"),
            selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
            unselected_color=("gray86", "gray24"),
            unselected_hover_color=("gray80", "gray28"),
            text_color=("gray20", "gray90"),
        )
        self._seg.set("归类")
        self._seg.pack(side="right", padx=16)

        # Thin separator under topbar
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        # Pages container
        self._pages = ctk.CTkFrame(self, fg_color="transparent")
        self._pages.pack(fill="both", expand=True)

        self._page_c = ctk.CTkFrame(self._pages, fg_color="transparent")
        self._page_d = ctk.CTkFrame(self._pages, fg_color="transparent")
        self._page_p = ctk.CTkFrame(self._pages, fg_color="transparent")

        self._build_classify_page(self._page_c)
        self._build_diagram_page(self._page_d)
        self._build_playlist_page(self._page_p)

        self._page_c.pack(fill="both", expand=True)

        # Status bar
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x", side="bottom")
        sbar = ctk.CTkFrame(self, fg_color=STATUS_BG, height=28, corner_radius=0)
        sbar.pack(fill="x", side="bottom")
        sbar.pack_propagate(False)

        self._s_dot  = ctk.CTkLabel(sbar, text="●", font=ctk.CTkFont(size=9),
                                     text_color="gray60", width=18)
        self._s_dot.pack(side="left", padx=(14, 2))
        self._s_text = ctk.CTkLabel(sbar, text="就绪", font=self.F_LABEL,
                                     text_color=SUBTLE, anchor="w")
        self._s_text.pack(side="left")

    def _switch_page(self, val: str):
        for p in (self._page_c, self._page_d, self._page_p):
            p.pack_forget()
        if val == "归类":
            self._page_c.pack(fill="both", expand=True)
        elif val == "图表":
            self._page_d.pack(fill="both", expand=True)
        else:
            self._page_p.pack(fill="both", expand=True)
        self._status("就绪", "gray60")

    def _status(self, msg: str, dot: str = "gray60"):
        self._s_dot.configure(text_color=dot)
        self._s_text.configure(text=msg)

    # ── Classify page ────────────────────────────────────────────────────────

    def _build_classify_page(self, page):
        P = 20  # horizontal padding

        ctk.CTkLabel(page, text="粘贴内容", font=self.F_LABEL, text_color=SUBTLE, anchor="w"
                     ).pack(fill="x", padx=P, pady=(18, 4))

        self._c_input = ctk.CTkTextbox(
            page, wrap="word", font=self.F_BODY,
            fg_color=INPUT_BG, border_color=BORDER, border_width=1, corner_radius=10,
        )
        self._c_input.pack(fill="both", expand=True, padx=P)

        self._c_btn = self._primary_btn(page, "分析归类", self._classify_start)
        self._c_btn.pack(fill="x", padx=P, pady=(10, 0))

        # Result card ─────────────────────────────────────────────────────
        self._c_card = ctk.CTkFrame(page, fg_color=CARD_BG, corner_radius=12,
                                     border_width=1, border_color=BORDER)
        # (packed later)

        # path row
        path_row = ctk.CTkFrame(self._c_card, fg_color="transparent")
        path_row.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(path_row, text="📁", font=self.F_BODY, width=22).pack(side="left")
        self._c_path = ctk.CTkLabel(path_row, text="", font=self.F_MONO,
                                     text_color=(ACCENT, "#8aaeff"),
                                     anchor="w", wraplength=380)
        self._c_path.pack(side="left", fill="x", expand=True)

        # reason
        self._c_reason = ctk.CTkLabel(self._c_card, text="", font=self.F_LABEL,
                                       text_color=SUBTLE, anchor="w",
                                       wraplength=418, justify="left")
        self._c_reason.pack(fill="x", padx=14, pady=(6, 0))

        # divider
        ctk.CTkFrame(self._c_card, height=1, fg_color=BORDER).pack(fill="x", padx=14, pady=10)

        # action buttons
        row = ctk.CTkFrame(self._c_card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 12))
        row.columnconfigure((0, 1), weight=1)

        self._primary_btn(row, "保存", self._classify_save, height=34
                          ).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self._ghost_btn(row, "取消", self._classify_cancel, height=34
                        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _classify_start(self):
        content = self._c_input.get("1.0", "end").strip()
        if not content:
            self._status("请先粘贴内容", ERROR)
            return
        self._c_btn.configure(state="disabled", text="分析中…")
        self._c_card.pack_forget()
        self._status("正在调用 DeepSeek 分析…", WARN)
        threading.Thread(target=self._classify_thread, args=(content,), daemon=True).start()

    def _classify_thread(self, content: str):
        try:
            qa = [{"question": "内容归类请求", "answer": content}]
            result = self.analyzer.analyze_placement(qa, "手动归类")
            self.after(0, self._classify_done, result)
        except Exception as e:
            self.after(0, self._classify_err, str(e))

    def _classify_done(self, result: dict):
        self._classify_result = result
        self._c_btn.configure(state="normal", text="分析归类")
        self._c_path.configure(text=result.get("target_path", ""))
        self._c_reason.configure(text=result.get("reasoning", ""))
        self._c_card.pack(fill="x", padx=20, pady=(10, 0))
        self._status("分析完成", SUCCESS)

    def _classify_err(self, msg: str):
        self._c_btn.configure(state="normal", text="分析归类")
        self._status(f"错误: {msg}", ERROR)

    def _classify_save(self):
        if not self._classify_result:
            return
        content = self._c_input.get("1.0", "end").strip()
        target  = self._classify_result["target_path"]
        full    = Path(self.config["obsidian"]["vault_path"]) / target
        full.parent.mkdir(parents=True, exist_ok=True)

        tags   = self._classify_result.get("tags", [])
        header = f"---\ntags: [{', '.join(tags)}]\ncreated: {datetime.now().isoformat()}\n---\n\n"
        try:
            full.write_text(header + content, encoding="utf-8")
            self._c_card.pack_forget()
            self._c_input.delete("1.0", "end")
            self._status(f"已保存 → {target}", SUCCESS)
        except Exception as e:
            self._status(f"保存失败: {e}", ERROR)

    def _classify_cancel(self):
        self._c_card.pack_forget()
        self._classify_result = None
        self._status("就绪", "gray60")

    # ── Diagram page ─────────────────────────────────────────────────────────

    def _build_diagram_page(self, page):
        P = 20

        ctk.CTkLabel(page, text="描述内容或概念", font=self.F_LABEL, text_color=SUBTLE, anchor="w"
                     ).pack(fill="x", padx=P, pady=(18, 4))

        self._d_input = ctk.CTkTextbox(
            page, height=88, wrap="word", font=self.F_BODY,
            fg_color=INPUT_BG, border_color=BORDER, border_width=1, corner_radius=10,
        )
        self._d_input.pack(fill="x", padx=P)

        self._d_btn = self._primary_btn(page, "生成图表", self._diagram_start)
        self._d_btn.pack(fill="x", padx=P, pady=(10, 0))

        # Image preview — expands to fill remaining space
        self._d_preview = ctk.CTkFrame(page, fg_color=CARD_BG, corner_radius=12,
                                        border_width=1, border_color=BORDER)
        self._d_preview.pack(fill="both", expand=True, padx=P, pady=12)

        self._d_img = ctk.CTkLabel(self._d_preview, text="图表预览",
                                    text_color=SUBTLE, font=self.F_LABEL)
        self._d_img.pack(fill="both", expand=True)

        # Redraw image when frame is resized
        self._d_preview.bind("<Configure>", self._on_preview_resize)

        # Action panel (hidden initially)
        self._d_action = ctk.CTkFrame(page, fg_color="transparent")

        ctk.CTkLabel(self._d_action, text="修改意见", font=self.F_LABEL,
                     text_color=SUBTLE, anchor="w").pack(fill="x", padx=P, pady=(0, 4))
        self._d_feedback = ctk.CTkEntry(
            self._d_action, height=34, font=self.F_BODY, corner_radius=8,
            fg_color=INPUT_BG, border_color=BORDER, border_width=1,
            placeholder_text="可选 — 留空直接重新生成",
        )
        self._d_feedback.pack(fill="x", padx=P)

        row = ctk.CTkFrame(self._d_action, fg_color="transparent")
        row.pack(fill="x", padx=P, pady=(8, 12))
        row.columnconfigure((0, 1), weight=1)

        self._d_regen_btn = self._ghost_btn(row, "重新生成", self._diagram_regen, height=34)
        self._d_regen_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self._d_save_btn = self._primary_btn(row, "保存到 Obsidian",
                                              self._diagram_save_start, height=34)
        self._d_save_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _diagram_start(self):
        content = self._d_input.get("1.0", "end").strip()
        if not content:
            self._status("请先输入内容", ERROR)
            return
        self._d_btn.configure(state="disabled", text="生成中…")
        self._d_action.pack_forget()
        self._d_img.configure(image=None, text="生成中…")
        self._status("正在调用 AI 生成可视化代码…", WARN)
        threading.Thread(target=self._diagram_thread, args=(content, None), daemon=True).start()

    def _diagram_regen(self):
        content  = self._d_input.get("1.0", "end").strip()
        feedback = self._d_feedback.get().strip() or None
        self._d_regen_btn.configure(state="disabled", text="重新生成中…")
        self._d_img.configure(image=None, text="重新生成中…")
        self._status("重新生成中…", WARN)
        threading.Thread(target=self._diagram_thread, args=(content, feedback), daemon=True).start()

    def _diagram_thread(self, content: str, feedback: str | None):
        raw = self.ai.call_api(self._diagram_prompt(content, feedback))
        if not raw:
            self.after(0, self._diagram_err, "AI 未返回响应")
            return
        py_code = extract_python_code(raw)
        if not py_code:
            self.after(0, self._diagram_err, "无法提取 Python 代码")
            return
        self._py_code = py_code
        self.after(0, lambda: self._status("执行 matplotlib 渲染中…", WARN))
        png, err = run_matplotlib_code(py_code)
        self._diagram_png = png
        self.after(0, self._diagram_done, png, err)

    def _diagram_done(self, png: bytes | None, err: str = ""):
        self._d_btn.configure(state="normal", text="生成图表")
        self._d_regen_btn.configure(state="normal", text="重新生成")

        if png:
            try:
                self._d_img.configure(text="")
                self._render_preview()          # resize to current frame dimensions
                self._status("图表生成成功", SUCCESS)
            except Exception as e:
                self._d_img.configure(image=None, text=f"PNG 解码失败: {e}")
                self._status("解码失败", WARN)
        else:
            short_err = err[:120] if err else "未知错误"
            self._d_img.configure(image=None, text=f"执行失败：\n{short_err}")
            self._status("脚本执行失败 — 可修改意见后重新生成", ERROR)

        self._d_action.pack(fill="x")

    def _render_preview(self):
        """将 _diagram_png 缩放到预览帧的实际尺寸并显示。"""
        if not self._diagram_png:
            return
        w = self._d_preview.winfo_width()  - 16
        h = self._d_preview.winfo_height() - 16
        if w < 50 or h < 50:
            w, h = 440, 340          # fallback before frame is rendered
        img = Image.open(io.BytesIO(self._diagram_png))
        img.thumbnail((w, h), Image.LANCZOS)
        ci = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        self._ctk_image = ci
        self._d_img.configure(image=ci)

    def _on_preview_resize(self, event):
        if self._diagram_png and event.width > 50 and event.height > 50:
            self._render_preview()

    def _diagram_err(self, msg: str):
        self._d_btn.configure(state="normal", text="生成图表")
        self._d_regen_btn.configure(state="normal", text="重新生成")
        self._d_img.configure(image=None, text="生成失败")
        self._status(f"错误: {msg}", ERROR)

    def _diagram_save_start(self):
        if not self._diagram_png:
            return
        self._d_save_btn.configure(state="disabled", text="保存中…")
        content = self._d_input.get("1.0", "end").strip()
        self._status("归类并保存中…", WARN)
        threading.Thread(target=self._diagram_save_thread, args=(content,), daemon=True).start()

    def _diagram_save_thread(self, content: str):
        try:
            qa = [{"question": content, "answer": f"图表说明：{content}"}]
            result = self.analyzer.analyze_placement(qa, "图表笔记")
            target = result["target_path"]
            full   = Path(self.config["obsidian"]["vault_path"]) / target
            full.parent.mkdir(parents=True, exist_ok=True)

            tags = result.get("tags", [])
            ts   = datetime.now()
            # PNG 保存在与 Markdown 相同的文件夹，用相对路径引用
            stem = Path(target).stem          # e.g. "黎曼积分"
            name = f"{stem}_viz.png"
            (full.parent / name).write_bytes(self._diagram_png)

            note = (
                f"---\ntags: [{', '.join(tags)}]\ncreated: {ts.isoformat()}\n---\n\n"
                f"# {content}\n\n"
                f"## 可视化\n\n"
                f"![{stem}]({name})\n"
            )

            full.write_text(note, encoding="utf-8")
            self.after(0, self._diagram_save_done, True, target)
        except Exception as e:
            self.after(0, self._diagram_save_done, False, str(e))

    def _diagram_save_done(self, ok: bool, info: str):
        self._d_save_btn.configure(state="normal", text="保存到 Obsidian")
        if ok:
            self._status(f"已保存 → {info}", SUCCESS)
        else:
            self._status(f"保存失败: {info}", ERROR)

    # ── Playlist page ─────────────────────────────────────────────────────────

    def _build_playlist_page(self, page):
        P = 20

        ctk.CTkLabel(page, text="课程 / 播放列表链接", font=self.F_LABEL,
                     text_color=SUBTLE, anchor="w").pack(fill="x", padx=P, pady=(18, 4))

        # URL input row
        url_row = ctk.CTkFrame(page, fg_color="transparent")
        url_row.pack(fill="x", padx=P)

        self._p_url = ctk.CTkEntry(
            url_row, height=36, font=self.F_BODY, corner_radius=8,
            fg_color=INPUT_BG, border_color=BORDER, border_width=1,
            placeholder_text="粘贴 YouTube 播放列表或课程链接…",
        )
        self._p_url.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._p_btn = self._primary_btn(url_row, "获取列表", self._playlist_start, height=36)
        self._p_btn.pack(side="right")

        # Count label + copy-all button row
        meta_row = ctk.CTkFrame(page, fg_color="transparent")
        meta_row.pack(fill="x", padx=P, pady=(10, 4))

        self._p_count = ctk.CTkLabel(meta_row, text="", font=self.F_LABEL,
                                      text_color=SUBTLE, anchor="w")
        self._p_count.pack(side="left")

        self._p_copy_all_btn = self._ghost_btn(meta_row, "复制全部链接",
                                                self._playlist_copy_all, height=26)
        self._p_copy_all_btn.pack(side="right")
        self._p_copy_all_btn.pack_forget()   # hidden until list is loaded

        # Scrollable list
        self._p_list = ctk.CTkScrollableFrame(page, fg_color="transparent", corner_radius=0)
        self._p_list.pack(fill="both", expand=True, padx=P, pady=(0, 8))

        self._p_videos: list[dict] = []   # [{title, url}, ...]

        # Restore last session
        self._playlist_load_cache()

    def _playlist_load_cache(self):
        """启动时从磁盘恢复上次的列表（静默失败）。"""
        try:
            if not PLAYLIST_CACHE.exists():
                return
            import json
            data = json.loads(PLAYLIST_CACHE.read_text(encoding="utf-8"))
            url     = data.get("url", "")
            videos  = data.get("videos", [])
            fetched = data.get("fetched", "")
            if not videos:
                return
            if url:
                self._p_url.delete(0, "end")
                self._p_url.insert(0, url)
            self._p_videos = videos
            self._p_count.configure(text=f"共 {len(videos)} 课  ·  上次获取 {fetched}")
            self._p_copy_all_btn.pack(side="right")
            for i, v in enumerate(videos):
                self._add_video_row(i + 1, v["title"], v["url"])
        except Exception:
            pass  # 缓存损坏时静默忽略

    def _playlist_save_cache(self, url: str):
        """将当前列表写入磁盘。"""
        import json
        try:
            PLAYLIST_CACHE.parent.mkdir(parents=True, exist_ok=True)
            PLAYLIST_CACHE.write_text(json.dumps({
                "url":     url,
                "videos":  self._p_videos,
                "fetched": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _playlist_start(self):
        url = self._p_url.get().strip()
        if not url:
            self._status("请先粘贴链接", ERROR)
            return
        self._p_btn.configure(state="disabled", text="获取中…")
        self._p_count.configure(text="")
        self._p_copy_all_btn.pack_forget()
        for w in self._p_list.winfo_children():
            w.destroy()
        self._p_videos = []
        self._status("正在调用 yt-dlp 获取课程列表…", WARN)
        threading.Thread(target=self._playlist_thread, args=(url,), daemon=True).start()

    def _playlist_thread(self, url: str):
        try:
            result = subprocess.run(
                ["yt-dlp", "--flat-playlist", "--print", "%(id)s|%(title)s", url],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "未知错误").strip()[-300:]
                self.after(0, self._playlist_err, err)
                return

            videos = []
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if "|" in line:
                    vid_id, title = line.split("|", 1)
                    videos.append({
                        "title": title.strip(),
                        "url": f"https://www.youtube.com/watch?v={vid_id.strip()}",
                    })
            self.after(0, self._playlist_done, videos)

        except FileNotFoundError:
            self.after(0, self._playlist_err, "yt-dlp 未找到，请确认已安装")
        except subprocess.TimeoutExpired:
            self.after(0, self._playlist_err, "获取超时（>60s），请检查网络")
        except Exception as e:
            self.after(0, self._playlist_err, str(e))

    def _playlist_done(self, videos: list[dict]):
        self._p_btn.configure(state="normal", text="获取列表")
        self._p_videos = videos
        n = len(videos)
        self._p_count.configure(text=f"共 {n} 课")
        self._status(f"获取完成，共 {n} 个视频", SUCCESS)

        if n == 0:
            self._status("未找到视频，检查链接是否为播放列表", WARN)
            return

        self._p_copy_all_btn.pack(side="right")
        for i, v in enumerate(videos):
            self._add_video_row(i + 1, v["title"], v["url"])

        # 持久化到磁盘
        self._playlist_save_cache(self._p_url.get().strip())

    def _playlist_err(self, msg: str):
        self._p_btn.configure(state="normal", text="获取列表")
        self._status(f"错误: {msg}", ERROR)

    def _add_video_row(self, idx: int, title: str, url: str):
        row = ctk.CTkFrame(self._p_list, fg_color=("white", "gray16"),
                           corner_radius=8, border_width=1, border_color=BORDER)
        row.pack(fill="x", pady=3)

        num = ctk.CTkLabel(row, text=f"{idx}", width=32, font=self.F_LABEL,
                           text_color=SUBTLE, anchor="center")
        num.pack(side="left", padx=(8, 0), pady=6)

        lbl = ctk.CTkLabel(row, text=title, font=self.F_LABEL, anchor="w",
                           wraplength=310, justify="left")
        lbl.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        btn = ctk.CTkButton(
            row, text="复制", width=44, height=24, corner_radius=6,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=("gray40", "gray70"), hover_color=("gray86", "gray26"),
            font=self.F_LABEL,
            command=lambda u=url, b=None, i=idx: self._copy_video(u, idx),
        )
        btn.pack(side="right", padx=8, pady=6)

    @staticmethod
    def _break_url(url: str) -> str:
        """在 .com/ 后插入空格，防止粘贴时被自动识别为视频链接。"""
        return url.replace("youtube.com/", "youtube.com/ ", 1)

    def _copy_video(self, url: str, idx: int):
        self.clipboard_clear()
        self.clipboard_append(self._break_url(url))
        self._status(f"已复制第 {idx} 课链接", SUCCESS)

    def _playlist_copy_all(self):
        if not self._p_videos:
            return
        text = "\n".join(f"{i+1}. {v['title']}\n   {self._break_url(v['url'])}"
                         for i, v in enumerate(self._p_videos))
        self.clipboard_clear()
        self.clipboard_append(text)
        self._status(f"已复制全部 {len(self._p_videos)} 条链接", SUCCESS)

    # ── Prompt ───────────────────────────────────────────────────────────────

    @staticmethod
    def _diagram_prompt(content: str, feedback: str | None) -> str:
        p = (
            f"请用 Python matplotlib 生成一张图，帮助理解以下内容：\n\n"
            f"{content}\n\n"
            f"⚠️ 严格要求：\n"
            f"1. 所有标签、标题、注释必须用英文（中文会乱码）\n"
            f"2. 选择最合适的图表类型（流程图用 patches+arrows、关系图用 networkx、数学图用 plot）\n"
            f"3. 最后一行必须是：plt.savefig('/tmp/knowledge_viz.png', dpi=150, bbox_inches='tight', facecolor='white')\n"
            f"4. 再加一行：plt.close()\n"
            f"5. 只返回 Python 代码块，不要任何解释：\n"
            f"```python\n...\n```"
        )
        if feedback:
            p += f"\n\n修改意见：{feedback}"
        return p

    # ── Button factories ─────────────────────────────────────────────────────

    def _primary_btn(self, parent, text, cmd, height=38):
        return ctk.CTkButton(
            parent, text=text, height=height, corner_radius=8,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=self.F_BTN, command=cmd,
        )

    def _ghost_btn(self, parent, text, cmd, height=38):
        return ctk.CTkButton(
            parent, text=text, height=height, corner_radius=8,
            fg_color="transparent", border_width=1, border_color=BORDER,
            text_color=("gray35", "gray70"), hover_color=("gray86", "gray26"),
            font=self.F_BTN, command=cmd,
        )


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    KnowledgeTool().mainloop()
