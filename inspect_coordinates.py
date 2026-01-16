from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from typing import Optional

from PIL import Image, ImageTk

IMAGE_PATH = Path("Can.jpg")
MIN_SCALE = 0.2
MAX_SCALE = 3.0
SCALE_STEP = 0.1


@dataclass
class SelectionState:
    start_screen: Optional[tuple[int, int]] = None
    start_image: Optional[tuple[int, int]] = None
    preview_id: Optional[int] = None


class CoordinateInspector:
    def __init__(self, image_path: Path) -> None:
        self.image_path = image_path
        self.state = SelectionState()
        self.root = tk.Tk()
        self.root.title(f"Coordinate Inspector - {image_path}")

        self.image = Image.open(image_path)
        self.scale = self._compute_initial_scale()
        self.scale_var = tk.DoubleVar(value=self.scale)
        self.photo: ImageTk.PhotoImage | None = None
        self.image_id: Optional[int] = None

        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack()
        self._render_image()

        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)

        info = tk.Label(
            self.root,
            text=(
                "Left-click to set the top-left corner, drag to the bottom-right, "
                "release to print the crop box coordinates. Use the slider or mouse wheel to zoom."
            ),
        )
        info.pack(pady=8)

        slider = tk.Scale(
            self.root,
            from_=MIN_SCALE,
            to=MAX_SCALE,
            resolution=SCALE_STEP,
            orient="horizontal",
            label="Zoom",
            variable=self.scale_var,
            command=self.on_scale_change,
        )
        slider.pack(fill="x", padx=12, pady=4)

        self.root.update_idletasks()
        self.root.minsize(self.canvas.winfo_width(), self.canvas.winfo_height() + 80)

    def _compute_initial_scale(self) -> float:
        screen_w = self.root.winfo_screenwidth() - 100
        screen_h = self.root.winfo_screenheight() - 200
        scale_w = screen_w / self.image.width
        scale_h = screen_h / self.image.height
        fit_scale = min(1.0, scale_w, scale_h)
        return max(MIN_SCALE, min(MAX_SCALE, fit_scale))

    def _render_image(self) -> None:
        width = max(1, int(self.image.width * self.scale))
        height = max(1, int(self.image.height * self.scale))
        display_image = self.image.resize((width, height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(display_image)
        self.canvas.config(width=width, height=height)
        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.state.preview_id = None

    def _screen_to_image(self, x: int, y: int) -> tuple[int, int]:
        return int(x / self.scale), int(y / self.scale)

    def on_scale_change(self, value: str) -> None:
        self.scale = float(value)
        self._render_image()

    def on_mousewheel(self, event: tk.Event) -> None:
        delta = 0
        if event.delta:
            delta = SCALE_STEP if event.delta > 0 else -SCALE_STEP
        elif event.num == 4:
            delta = SCALE_STEP
        elif event.num == 5:
            delta = -SCALE_STEP
        if not delta:
            return
        new_scale = max(MIN_SCALE, min(MAX_SCALE, self.scale + delta))
        if abs(new_scale - self.scale) < 1e-9:
            return
        self.scale = new_scale
        self.scale_var.set(round(self.scale, 2))
        self._render_image()

    def on_button_press(self, event: tk.Event) -> None:
        self.state.start_screen = (event.x, event.y)
        self.state.start_image = self._screen_to_image(event.x, event.y)
        print(f"Start (image coords): {self.state.start_image}")
        if self.state.preview_id is not None:
            self.canvas.delete(self.state.preview_id)
            self.state.preview_id = None

    def on_drag(self, event: tk.Event) -> None:
        if self.state.start_screen is None:
            return
        x1, y1 = self.state.start_screen
        x2, y2 = event.x, event.y
        if self.state.preview_id is not None:
            self.canvas.coords(self.state.preview_id, x1, y1, x2, y2)
        else:
            self.state.preview_id = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline="red",
                dash=(4, 2),
                width=2,
            )

    def on_button_release(self, event: tk.Event) -> None:
        if self.state.start_image is None:
            return
        end_image = self._screen_to_image(event.x, event.y)
        sx, sy = self.state.start_image
        ex, ey = end_image
        x_min, y_min = min(sx, ex), min(sy, ey)
        x_max, y_max = max(sx, ex), max(sy, ey)
        print(f"CROP_BOX = ({x_min}, {y_min}, {x_max}, {y_max})")
        self.state.start_screen = None
        self.state.start_image = None
        if self.state.preview_id is not None:
            self.canvas.delete(self.state.preview_id)
            self.state.preview_id = None

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"Cannot find image at {IMAGE_PATH.resolve()}")
    inspector = CoordinateInspector(IMAGE_PATH)
    inspector.run()


if __name__ == "__main__":
    main()
