from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw


DEFAULT_CELL_SIZE = 20
DEFAULT_GRID_HEIGHT = 20
DEFAULT_GRID_WIDTH = 20
MIN_CELL_SIZE = 4
MAX_CELL_SIZE = 80


def create_blank_map(height: int, width: int) -> np.ndarray:
    """Create an empty binary occupancy grid.

    Args:
        height: Number of map rows.
        width: Number of map columns.

    Returns:
        `uint8` array filled with zeros, where 0 means free space.
    """
    return np.zeros((int(height), int(width)), dtype=np.uint8)


def create_map_canvas(height: int, width: int, cell_size: int = DEFAULT_CELL_SIZE) -> Image.Image:
    """Create a blank visualization canvas for one binary occupancy grid.

    Args:
        height: Number of map rows.
        width: Number of map columns.
        cell_size: Pixel size used to visualize one grid cell.

    Returns:
        White RGB image with light-gray grid lines.
    """
    canvas_width = int(width) * int(cell_size)
    canvas_height = int(height) * int(cell_size)
    image = Image.new("RGB", (canvas_width, canvas_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    for x in range(0, canvas_width + 1, int(cell_size)):
        draw.line([(x, 0), (x, canvas_height)], fill=(225, 225, 225), width=1)
    for y in range(0, canvas_height + 1, int(cell_size)):
        draw.line([(0, y), (canvas_width, y)], fill=(225, 225, 225), width=1)

    return image


def sketch_to_map(
    sketch: np.ndarray | Image.Image | None,
    height: int,
    width: int,
    cell_size: int = DEFAULT_CELL_SIZE,
) -> np.ndarray:
    """Convert a drawn sketch canvas into a binary occupancy grid.

    Args:
        sketch: Drawn sketch as a numpy array or PIL image.
        height: Number of map rows.
        width: Number of map columns.
        cell_size: Pixel size used to visualize one grid cell.

    Returns:
        `uint8` grid where 0 is free space and 1 is obstacle.
    """
    grid = create_blank_map(height=height, width=width)
    if sketch is None:
        return grid

    image_array = np.asarray(sketch) if isinstance(sketch, Image.Image) else np.asarray(sketch)
    if image_array.ndim == 2:
        mask = image_array < 128
    else:
        mask = np.mean(image_array[:, :, :3], axis=2) < 128

    for row in range(int(height)):
        for col in range(int(width)):
            cell = mask[
                row * int(cell_size):(row + 1) * int(cell_size),
                col * int(cell_size):(col + 1) * int(cell_size),
            ]
            if cell.size and np.any(cell):
                grid[row, col] = 1

    return grid


def save_map_data(
    grid: np.ndarray,
    output_path: str | Path,
    output_format: Literal["json", "npy"],
) -> Path:
    """Save one binary occupancy grid to disk.

    Args:
        grid: Binary occupancy grid where 0 is free and 1 is obstacle.
        output_path: Target filesystem path.
        output_format: Output format, either `json` or `npy`.

    Returns:
        Final filesystem path that was written.
    """
    path = Path(output_path)
    suffix = f".{output_format}"
    if path.suffix.lower() != suffix:
        path = path.with_suffix(suffix)
    path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        path.write_text(json.dumps(grid.tolist()), encoding="utf-8")
    else:
        np.save(path, grid)

    return path


def add_map_border(grid: np.ndarray) -> np.ndarray:
    """Set the outer border cells of one map to obstacle value `1`.

    Args:
        grid: Binary occupancy grid where 0 is free and 1 is obstacle.

    Returns:
        Copy of the grid with the outer ring set to 1.
    """
    bordered = np.array(grid, copy=True, dtype=np.uint8)
    if bordered.size == 0:
        return bordered
    bordered[0, :] = 1
    bordered[-1, :] = 1
    bordered[:, 0] = 1
    bordered[:, -1] = 1
    return bordered


def fill_map_cell(grid: np.ndarray, row: int, col: int) -> np.ndarray:
    """Set one target cell to obstacle value `1`.

    Args:
        grid: Binary occupancy grid where 0 is free and 1 is obstacle.
        row: Target row index.
        col: Target column index.

    Returns:
        Copy of the grid with the target cell set to 1 when in bounds.
    """
    filled = np.array(grid, copy=True, dtype=np.uint8)
    if 0 <= row < filled.shape[0] and 0 <= col < filled.shape[1]:
        filled[row, col] = 1
    return filled


def erase_map_cell(grid: np.ndarray, row: int, col: int) -> np.ndarray:
    """Set one target cell to free-space value `0`.

    Args:
        grid: Binary occupancy grid where 0 is free and 1 is obstacle.
        row: Target row index.
        col: Target column index.

    Returns:
        Copy of the grid with the target cell set to 0 when in bounds.
    """
    erased = np.array(grid, copy=True, dtype=np.uint8)
    if 0 <= row < erased.shape[0] and 0 <= col < erased.shape[1]:
        erased[row, col] = 0
    return erased


def reset_map_obstacles(grid: np.ndarray) -> np.ndarray:
    """Clear all obstacle cells from one map.

    Args:
        grid: Binary occupancy grid where 0 is free and 1 is obstacle.

    Returns:
        Zero-filled grid with the same shape as the input.
    """
    return np.zeros_like(grid, dtype=np.uint8)


def random_fill_obstacles(
    grid: np.ndarray,
    obstacle_ratio: float,
    seed: int | None = None,
) -> np.ndarray:
    """Randomly mark sampled cells as obstacles using one ratio parameter.

    Args:
        grid: Binary occupancy grid where 0 is free and 1 is obstacle.
        obstacle_ratio: Fraction of coordinates to sample in `[0.0, 1.0]`.
        seed: Optional RNG seed for deterministic sampling.

    Returns:
        Copy of the grid with sampled coordinates set to obstacle value `1`.
    """
    filled = np.array(grid, copy=True, dtype=np.uint8)
    total_cells = int(filled.size)
    sample_count = max(0, min(total_cells, int(round(total_cells * float(obstacle_ratio)))))
    if sample_count == 0:
        return filled

    rng = np.random.default_rng(seed)
    sampled_indices = rng.choice(total_cells, size=sample_count, replace=False)
    filled.reshape(-1)[sampled_indices] = 1
    return filled


def scale_cell_size(current_cell_size: int, delta: int) -> int:
    """Adjust the display cell size while keeping map data unchanged.

    Args:
        current_cell_size: Current visualization size of one cell in pixels.
        delta: Signed zoom step count; positive zooms in and negative zooms out.

    Returns:
        Clamped cell size used only for display.
    """
    return max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, int(current_cell_size) + int(delta) * 2))


def render_map_preview(grid: np.ndarray, cell_size: int = DEFAULT_CELL_SIZE) -> Image.Image:
    """Render a binary occupancy grid into a preview image.

    Args:
        grid: Binary occupancy grid where 0 is free and 1 is obstacle.
        cell_size: Pixel size used to visualize one grid cell.

    Returns:
        RGB image showing free cells in white and obstacles in black.
    """
    height, width = grid.shape
    image = Image.new("RGB", (width * cell_size, height * cell_size), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    for row in range(height):
        for col in range(width):
            if int(grid[row, col]) == 1:
                left = col * cell_size
                top = row * cell_size
                draw.rectangle(
                    [left, top, left + cell_size - 1, top + cell_size - 1],
                    fill=(0, 0, 0),
                )

    for x in range(0, width * cell_size + 1, cell_size):
        draw.line([(x, 0), (x, height * cell_size)], fill=(225, 225, 225), width=1)
    for y in range(0, height * cell_size + 1, cell_size):
        draw.line([(0, y), (width * cell_size, y)], fill=(225, 225, 225), width=1)

    return image


class MapDrawerApp:
    """Local desktop tool for painting binary occupancy maps.

    Attributes:
        root: Tk root window that owns the local UI.
        grid: Current binary occupancy grid where 0 is free and 1 is obstacle.
        cell_size: Pixel size used to visualize one grid cell.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the local map drawer UI.

        Args:
            root: Tk root window.

        Returns:
            None.
        """
        self.root = root
        self.root.title("Map Drawer")
        self.cell_size = DEFAULT_CELL_SIZE
        self.grid = create_blank_map(DEFAULT_GRID_HEIGHT, DEFAULT_GRID_WIDTH)

        self.height_var = tk.IntVar(value=DEFAULT_GRID_HEIGHT)
        self.width_var = tk.IntVar(value=DEFAULT_GRID_WIDTH)
        self.random_ratio_var = tk.DoubleVar(value=0.10)
        self.format_var = tk.StringVar(value="json")
        self.path_var = tk.StringVar(value="maps/drawn_map")
        self.status_var = tk.StringVar(value="Ready")

        self._build_controls()
        self._build_canvas()
        self._redraw_canvas()

    def _build_controls(self) -> None:
        """Build the control panel widgets.

        Args:
            None.

        Returns:
            None.
        """
        controls = ttk.Frame(self.root, padding=12)
        controls.grid(row=0, column=0, sticky="nsew")

        ttk.Label(controls, text="Map Height").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(controls, from_=1, to=500, textvariable=self.height_var, width=8).grid(row=0, column=1, sticky="w")
        ttk.Label(controls, text="Map Width").grid(row=1, column=0, sticky="w")
        ttk.Spinbox(controls, from_=1, to=500, textvariable=self.width_var, width=8).grid(row=1, column=1, sticky="w")
        ttk.Button(controls, text="Create Blank Map", command=self.reset_map).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Label(controls, text="Save Path").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(controls, textvariable=self.path_var, width=28).grid(row=4, column=0, columnspan=2, sticky="ew")
        ttk.Button(controls, text="Browse", command=self.choose_save_path).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        ttk.Button(controls, text="Add Border", command=self.add_border).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Label(controls, text="Random Obstacle Ratio").grid(row=7, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(controls, from_=0.0, to=1.0, increment=0.01, textvariable=self.random_ratio_var, width=8).grid(row=7, column=1, sticky="w", pady=(12, 0))
        ttk.Button(controls, text="Random Fill", command=self.random_fill).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ttk.Button(controls, text="Clear Obstacles", command=self.clear_obstacles).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        ttk.Label(controls, text="Save Format").grid(row=10, column=0, sticky="w", pady=(12, 0))
        ttk.Combobox(controls, textvariable=self.format_var, values=("json", "npy"), state="readonly", width=10).grid(row=10, column=1, sticky="w", pady=(12, 0))
        ttk.Button(controls, text="Save Map", command=self.save_map).grid(row=11, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Label(controls, textvariable=self.status_var, wraplength=220).grid(row=12, column=0, columnspan=2, sticky="w", pady=(12, 0))

        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

    def _build_canvas(self) -> None:
        """Build the drawing canvas.

        Args:
            None.

        Returns:
            None.
        """
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.grid(row=0, column=1, padx=12, pady=12, sticky="nsew")

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.grid.shape[1] * self.cell_size,
            height=self.grid.shape[0] * self.cell_size,
            background="white",
            highlightthickness=1,
            highlightbackground="#cccccc",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        x_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        y_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        self.canvas.bind("<Button-1>", self.paint_cell)
        self.canvas.bind("<B1-Motion>", self.paint_cell)
        self.canvas.bind("<Button-3>", self.erase_cell)
        self.canvas.bind("<B3-Motion>", self.erase_cell)
        self.canvas.bind("<MouseWheel>", self.zoom_canvas)
        self.canvas.bind("<Button-4>", self.zoom_canvas)
        self.canvas.bind("<Button-5>", self.zoom_canvas)

        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

    def reset_map(self) -> None:
        """Create a new blank map using the configured dimensions.

        Args:
            None.

        Returns:
            None.
        """
        height = max(int(self.height_var.get()), 1)
        width = max(int(self.width_var.get()), 1)
        self.grid = create_blank_map(height=height, width=width)
        self._redraw_canvas()
        self.status_var.set(f"Created blank {height}x{width} map.")

    def add_border(self) -> None:
        """Set the outer border cells to obstacle value `1`.

        Args:
            None.

        Returns:
            None.
        """
        self.grid = add_map_border(self.grid)
        self._redraw_canvas()
        self.status_var.set("Added obstacle border.")

    def random_fill(self) -> None:
        """Randomly sample cells and mark them as obstacles.

        Args:
            None.

        Returns:
            None.
        """
        ratio = min(max(float(self.random_ratio_var.get()), 0.0), 1.0)
        self.grid = random_fill_obstacles(self.grid, obstacle_ratio=ratio)
        self._redraw_canvas()
        self.status_var.set(f"Randomly filled obstacles with ratio {ratio:.2f}.")

    def clear_obstacles(self) -> None:
        """Clear all painted obstacle cells.

        Args:
            None.

        Returns:
            None.
        """
        self.grid = reset_map_obstacles(self.grid)
        self._redraw_canvas()
        self.status_var.set("Cleared all obstacles.")

    def paint_cell(self, event: tk.Event) -> None:
        """Mark the cell under the pointer as an obstacle.

        Args:
            event: Tk pointer event carrying canvas coordinates.

        Returns:
            None.
        """
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        self.grid = fill_map_cell(self.grid, row=row, col=col)
        self._draw_cell(row=row, col=col)
        self.status_var.set(f"Obstacle cells: {int(self.grid.sum())}")

    def erase_cell(self, event: tk.Event) -> None:
        """Clear the cell under the pointer back to free space.

        Args:
            event: Tk pointer event carrying canvas coordinates.

        Returns:
            None.
        """
        col = event.x // self.cell_size
        row = event.y // self.cell_size
        self.grid = erase_map_cell(self.grid, row=row, col=col)
        self._draw_cell(row=row, col=col)
        self.status_var.set(f"Obstacle cells: {int(self.grid.sum())}")

    def zoom_canvas(self, event: tk.Event) -> None:
        """Zoom the canvas display without changing the underlying grid.

        Args:
            event: Tk wheel event carrying zoom direction.

        Returns:
            None.
        """
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            delta = 1
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            delta = -1
        else:
            return
        self.cell_size = scale_cell_size(self.cell_size, delta)
        self._redraw_canvas()
        self.status_var.set(f"Zoom: cell size {self.cell_size}px")

    def choose_save_path(self) -> None:
        """Open a native save dialog and store the chosen path.

        Args:
            None.

        Returns:
            None.
        """
        filetypes = [("JSON", "*.json"), ("NumPy", "*.npy")]
        selected_path = filedialog.asksaveasfilename(
            title="Save Map",
            initialfile=Path(self.path_var.get()).name,
            initialdir=str(Path(self.path_var.get()).parent),
            filetypes=filetypes,
            defaultextension=f".{self.format_var.get()}",
        )
        if selected_path:
            self.path_var.set(selected_path)

    def save_map(self) -> None:
        """Save the current grid using the selected path and format.

        Args:
            None.

        Returns:
            None.
        """
        save_path = self.path_var.get().strip()
        if not save_path:
            messagebox.showerror("Map Drawer", "Please choose a save path before saving.")
            return

        saved_path = save_map_data(
            grid=self.grid,
            output_path=save_path,
            output_format=self.format_var.get(),
        )
        self.path_var.set(str(saved_path))
        self.status_var.set(f"Saved map to {saved_path}")

    def _redraw_canvas(self) -> None:
        """Redraw the complete grid on the canvas.

        Args:
            None.

        Returns:
            None.
        """
        self.canvas.delete("all")
        self.canvas.config(
            width=min(self.grid.shape[1] * self.cell_size, 1000),
            height=min(self.grid.shape[0] * self.cell_size, 800),
        )
        self.canvas.configure(
            scrollregion=(0, 0, self.grid.shape[1] * self.cell_size, self.grid.shape[0] * self.cell_size)
        )
        for row in range(self.grid.shape[0]):
            for col in range(self.grid.shape[1]):
                self._draw_cell(row=row, col=col)

    def _draw_cell(self, row: int, col: int) -> None:
        """Draw one cell rectangle using the current occupancy value.

        Args:
            row: Cell row index.
            col: Cell column index.

        Returns:
            None.
        """
        left = col * self.cell_size
        top = row * self.cell_size
        right = left + self.cell_size
        bottom = top + self.cell_size
        fill = "black" if int(self.grid[row, col]) == 1 else "white"
        self.canvas.create_rectangle(left, top, right, bottom, fill=fill, outline="#dddddd")


def main() -> None:
    """Launch the local desktop map drawer tool.

    Args:
        None.

    Returns:
        None. This function blocks while the desktop window is open.
    """
    root = tk.Tk()
    MapDrawerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
