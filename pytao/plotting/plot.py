from __future__ import annotations
import logging
import math
from typing import Dict, List, Literal, Optional, Tuple, TypedDict, Union, cast

import matplotlib.axes
import matplotlib.collections
import matplotlib.patches
import matplotlib.path
import matplotlib.pyplot as plt
import numpy as np
from pytao import Tao

from . import pgplot, util

import pydantic.dataclasses as dataclasses
from pydantic.dataclasses import Field

from typing_extensions import NotRequired

logger = logging.getLogger(__name__)


class GraphInvalidError(Exception):
    pass


class NoCurveDataError(Exception):
    pass


def _fix_limits(lim: Point) -> Point:
    low, high = lim
    if np.isclose(low, 0.0) and np.isclose(high, 0.0):
        # TODO: matplotlib can sometimes get in a bad spot trying to plot empty data
        # with very small limits
        return (-0.001, 0.001)
    return (low, high)


FloorOrbitInfo = TypedDict(
    "FloorOrbitInfo",
    {
        "branch_index": int,
        "index": int,
        "ele_key": str,
        "axis": str,
        "orbits": List[float],
    },
)
BuildingWallGraphInfo = TypedDict(
    "BuildingWallGraphInfo",
    {
        "index": int,
        "point": int,
        "offset_x": float,
        "offset_y": float,
        "radius": float,
    },
)

BuildingWallInfo = TypedDict(
    "BuildingWallInfo",
    {
        "index": int,
        "z": float,
        "x": float,
        "radius": float,
        "z_center": float,
        "x_center": float,
    },
)

WaveParams = TypedDict(
    "WaveParams",
    {
        "ix_a1": float,
        "ix_a2": float,
        "ix_b1": float,
        "ix_b2": float,
    },
)

PlotCurveLineInfo = TypedDict(
    "PlotCurveLineInfo",
    {
        "color": str,
        "line^pattern": str,
        "width": int,
    },
)

PlotCurveSymbolInfo = TypedDict(
    "PlotCurveSymbolInfo",
    {
        "color": str,
        "fill_pattern": str,
        "height": float,
        "line_width": int,
        "symbol^type": str,
    },
)
PlotCurveInfo = TypedDict(
    "PlotCurveInfo",
    {
        "-1^ix_branch": int,
        "-1^ix_bunch": int,
        "component": str,
        "data_source": str,
        "data_type": str,
        "data_type_x": str,
        "draw_error_bars": bool,
        "draw_line": bool,
        "draw_symbol_index": bool,
        "draw_symbols": bool,
        "ele_ref_name": str,
        "ix_ele_ref": int,
        "ix_ele_ref_track": int,
        "ix_universe": int,
        "legend_text": str,
        "line": PlotCurveLineInfo,
        "message_text": str,
        "name": str,
        "smooth_line_calc": bool,
        "symbol": PlotCurveSymbolInfo,
        "symbol_every": int,
        "symbol_line_width": int,
        "use_y2": bool,
        "valid": bool,
        "why_invalid": str,
        "y_axis_scale_factor": float,
        "z_color_autoscale": bool,
        "z_color_data_type": str,
        "z_color_is_on": bool,
        "z_color_max": float,
        "z_color_min": float,
    },
)


PlotGraphInfo = TypedDict(
    "PlotGraphInfo",
    {
        "-1^ix_branch": int,
        "clip": bool,
        "draw_axes": bool,
        "draw_curve_legend": bool,
        "draw_grid": bool,
        "draw_only_good_user_data_or_vars": bool,
        "floor_plan_correct_distortion": bool,
        "floor_plan_draw_building_wall": bool,
        "floor_plan_draw_only_first_pass": bool,
        "floor_plan_flip_label_side": bool,
        "floor_plan_orbit_color": str,
        "floor_plan_orbit_lattice": str,
        "floor_plan_orbit_pattern": str,
        "floor_plan_orbit_scale": float,
        "floor_plan_orbit_width": int,
        "floor_plan_rotation": float,
        "floor_plan_size_is_absolute": bool,
        "floor_plan_view": str,
        "graph^type": str,
        "is_valid": bool,
        "ix_universe": int,
        "limited": bool,
        "name": str,
        "num_curves": int,
        "symbol_size_scale": float,
        "title": str,
        "title_suffix": str,
        "why_invalid": str,
        "x_axis^type": str,
        "x_axis_scale_factor": float,
        "x_bounds": str,
        "x_draw_label": bool,
        "x_draw_numbers": bool,
        "x_label": str,
        "x_label_color": str,
        "x_label_offset": float,
        "x_major_div_nominal": int,
        "x_major_tick_len": float,
        "x_max": float,
        "x_min": float,
        "x_minor_div": int,
        "x_minor_div_max": int,
        "x_minor_tick_len": float,
        "x_number_offset": float,
        "x_number_side": int,
        "x_tick_side": int,
        "y2_axis^type": str,
        "y2_bounds": str,
        "y2_draw_label": bool,
        "y2_draw_numbers": bool,
        "y2_label": str,
        "y2_label_color": str,
        "y2_label_offset": float,
        "y2_major_div_nominal": int,
        "y2_major_tick_len": float,
        "y2_max": float,
        "y2_min": float,
        "y2_minor_div": int,
        "y2_minor_div_max": int,
        "y2_minor_tick_len": float,
        "y2_mirrors_y": bool,
        "y2_number_offset": float,
        "y2_number_side": int,
        "y2_tick_side": int,
        "y_axis^type": str,
        "y_bounds": str,
        "y_draw_label": bool,
        "y_draw_numbers": bool,
        "y_label": str,
        "y_label_color": str,
        "y_label_offset": float,
        "y_major_div_nominal": int,
        "y_major_tick_len": float,
        "y_max": float,
        "y_min": float,
        "y_minor_div": int,
        "y_minor_div_max": int,
        "y_minor_tick_len": float,
        "y_number_offset": float,
        "y_number_side": int,
        "y_tick_side": int,
        # "curve[1..N]": str,
    },
)


PlotHistogramInfo = TypedDict(
    "PlotHistogramInfo",
    {
        "center": float,
        "density_normalized": bool,
        "maximum": float,
        "minimum": float,
        "number": float,
        "weight_by_charge": bool,
        "width": float,
    },
)

PlotLatLayoutInfo = TypedDict(
    "PlotLatLayoutInfo",
    {
        "color": str,
        "ele_s": float,
        "ele_s_start": float,
        "index": int,
        "label_name": str,
        "line_width": float,
        "shape": str,
        "y1": float,
        "y2": float,
    },
)

FloorPlanElementInfo = TypedDict(
    "FloorPlanElementInfo",
    {
        "branch_index": int,
        "color": str,
        "ele_key": str,
        "end1_r1": float,
        "end1_r2": float,
        "end1_theta": float,
        "end2_r1": float,
        "end2_r2": float,
        "end2_theta": float,
        "index": int,
        "label_name": str,
        "line_width": float,
        "shape": str,
        "y1": float,
        "y2": float,
        # Only for sbend
        "ele_l": NotRequired[float],
        "ele_angle": NotRequired[float],
        "ele_e1": NotRequired[float],
        "ele_e": NotRequired[float],
    },
)


Point = Tuple[float, float]


def print_info(d):
    print({key: type(value).__name__ for key, value in d.items()})
    for key, value in d.items():
        if isinstance(value, dict):
            print(key, "->")
            print_info(value)


def _should_use_symbol_color(symbol_type: str, fill_pattern: str) -> bool:
    if (
        symbol_type in ("dot", "1")
        or symbol_type.endswith("filled")
        or symbol_type.startswith("-")
    ):
        return True

    if pgplot.fills[fill_pattern] == "solid":
        return True

    return False


@dataclasses.dataclass
class PlotAnnotation:
    x: float
    y: float
    text: str
    horizontalalignment: str = "left"
    verticalalignment: str = "baseline"
    clip_on: bool = False
    color: str = "black"
    rotation: float = 0
    rotation_mode: str = "default"

    def plot(self, ax: matplotlib.axes.Axes):
        return ax.text(
            x=self.x,
            y=self.y,
            s=self.text,
            horizontalalignment=self.horizontalalignment,
            verticalalignment=self.verticalalignment,
            clip_on=self.clip_on,
            color=self.color,
            rotation=self.rotation,
            rotation_mode=self.rotation_mode,
        )


@dataclasses.dataclass
class PlotCurveLine:
    xs: List[float]
    ys: List[float]
    color: str = "black"
    linestyle: str = "solid"
    linewidth: float = 1.0

    def plot(self, ax: matplotlib.axes.Axes):
        return ax.plot(
            self.xs,
            self.ys,
            color=self.color,
            linestyle=self.linestyle,
            linewidth=self.linewidth,
        )


@dataclasses.dataclass
class PlotCurveSymbols:
    xs: List[float]
    ys: List[float]
    color: str
    markerfacecolor: str
    markersize: float
    marker: str
    markeredgewidth: float
    linewidth: float = 0

    def plot(self, ax: matplotlib.axes.Axes):
        return ax.plot(
            self.xs,
            self.ys,
            color=self.color,
            markerfacecolor=self.markerfacecolor,
            markersize=self.markersize,
            marker=self.marker,
            markeredgewidth=self.markeredgewidth,
            linewidth=self.linewidth,
        )


@dataclasses.dataclass
class PlotHistogram:
    xs: List[float]
    bins: float
    weights: List[float]
    histtype: str
    color: str

    def plot(self, ax: matplotlib.axes.Axes) -> None:
        return ax.hist(
            self.xs,
            bins=self.bins,
            weights=self.weights,
            histtype=self.histtype,
            color=self.color,
        )


@dataclasses.dataclass
class PlotPatchBase:
    edgecolor: Optional[str] = None
    facecolor: Optional[str] = None
    color: Optional[str] = None
    linewidth: Optional[float] = None
    linestyle: Optional[str] = None
    antialiased: Optional[bool] = None
    hatch: Optional[str] = None
    fill: bool = True
    capstyle: Optional[str] = None
    joinstyle: Optional[str] = None
    alpha: float = 1.0

    @property
    def _patch_args(self):
        return {
            "edgecolor": self.edgecolor,
            "facecolor": self.facecolor,
            "color": self.color,
            "linewidth": self.linewidth,
            "linestyle": self.linestyle,
            "antialiased": self.antialiased,
            "hatch": self.hatch,
            "fill": self.fill,
            "capstyle": self.capstyle,
            "joinstyle": self.joinstyle,
            "alpha": self.alpha,
        }

    def to_mpl(self):
        raise NotImplementedError(type(self))

    def plot(self, ax: matplotlib.axes.Axes):
        mpl = self.to_mpl()
        ax.add_patch(mpl)
        return mpl


_point_field = Field(default_factory=lambda: (0.0, 0.0))


@dataclasses.dataclass
class PlotPatchRectangle(PlotPatchBase):
    xy: Point = _point_field
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0
    rotation_point: str = "xy"

    def to_mpl(self) -> matplotlib.patches.Rectangle:
        return matplotlib.patches.Rectangle(
            xy=self.xy,
            width=self.width,
            height=self.height,
            angle=self.angle,
            rotation_point=self.rotation_point,
            **self._patch_args,
        )


@dataclasses.dataclass
class PlotPatchArc(PlotPatchBase):
    xy: Point = _point_field
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0
    theta1: float = 0.0
    theta2: float = 360.0

    def to_mpl(self) -> matplotlib.patches.Arc:
        return matplotlib.patches.Arc(
            xy=self.xy,
            width=self.width,
            height=self.height,
            angle=self.angle,
            theta1=self.theta1,
            theta2=self.theta2,
            **self._patch_args,
        )


@dataclasses.dataclass
class PlotPatchCircle(PlotPatchBase):
    xy: Point = _point_field
    radius: float = 0.0

    def to_mpl(self) -> matplotlib.patches.Ellipse:
        return matplotlib.patches.Circle(
            xy=self.xy,
            radius=self.radius,
            **self._patch_args,
        )


@dataclasses.dataclass
class PlotPatchEllipse(PlotPatchBase):
    xy: Point = _point_field
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0

    def to_mpl(self) -> matplotlib.patches.Ellipse:
        return matplotlib.patches.Ellipse(
            xy=self.xy,
            width=self.width,
            height=self.height,
            angle=self.angle,
            **self._patch_args,
        )


CustomPathCommand = Literal[
    "STOP",
    "MOVETO",
    "LINETO",
    "CURVE3",
    "CURVE4",
    "CLOSEPOLY",
]

_command_to_mpl_path = {
    "STOP": matplotlib.path.Path.STOP,
    "MOVETO": matplotlib.path.Path.MOVETO,
    "LINETO": matplotlib.path.Path.LINETO,
    "CURVE3": matplotlib.path.Path.CURVE3,
    "CURVE4": matplotlib.path.Path.CURVE4,
    "CLOSEPOLY": matplotlib.path.Path.CLOSEPOLY,
}


@dataclasses.dataclass
class PlotPatchCustom(PlotPatchBase):
    commands: List[CustomPathCommand] = Field(default_factory=list)
    vertices: List[List[Point]] = Field(default_factory=list)

    @property
    def mpl_path_codes(self):
        return [_command_to_mpl_path[cmd] for cmd in self.commands]

    def to_mpl(self) -> matplotlib.patches.PathPatch:
        path = matplotlib.path.Path(self.vertices, self.mpl_path_codes)
        return matplotlib.patches.PathPatch(path, facecolor="green", alpha=0.5)


PlotPatch = Union[
    PlotPatchRectangle,
    PlotPatchArc,
    PlotPatchCircle,
    PlotPatchEllipse,
    PlotPatchCustom,
]


@dataclasses.dataclass
class PlotCurve:
    info: PlotCurveInfo
    line: Optional[PlotCurveLine]
    symbol: Optional[PlotCurveSymbols]
    histogram: Optional[PlotHistogram] = None
    patches: Optional[List[PlotPatch]] = None

    def plot(self, ax: matplotlib.axes.Axes) -> None:
        if self.line is not None:
            self.line.plot(ax)
        if self.symbol is not None:
            self.symbol.plot(ax)
        if self.histogram is not None:
            self.histogram.plot(ax)
        for patch in self.patches or []:
            patch.plot(ax)

    @property
    def legend_label(self) -> str:
        legend_text = pgplot.mpl_string(self.info["legend_text"])
        if legend_text:
            return legend_text

        data_type = pgplot.mpl_string(self.info["data_type"])
        return data_type if data_type == "physical_aperture" else ""

    @classmethod
    def from_tao(
        cls,
        tao: Tao,
        region_name: str,
        graph_name: str,
        curve_name: str,
        graph_type: Optional[str] = None,
    ) -> PlotCurve:
        full_name = f"{region_name}.{graph_name}.{curve_name}"
        curve_info = cast(PlotCurveInfo, tao.plot_curve(full_name))
        points = [
            (line["x"], line["y"])
            for line in tao.plot_line(region_name, graph_name, curve_name) or []
        ]
        try:
            symbol_points = [
                (sym["x_symb"], sym["y_symb"])
                for sym in tao.plot_symbol(region_name, graph_name, curve_name, x_or_y="")
                or []
            ]
        except RuntimeError:
            symbol_points = []

        if graph_type is None:
            graph_info = cast(PlotGraphInfo, tao.plot_graph(f"{region_name}.{graph_name}"))
            graph_type = graph_info["graph^type"]

        if graph_type == "histogram":
            histogram_info = cast(PlotHistogramInfo, tao.plot_histogram(full_name))
        else:
            histogram_info = None

        wave_params = cast(WaveParams, tao.wave("params"))
        return cls.from_info(
            graph_type=graph_type,
            curve_info=curve_info,
            points=points,
            symbol_points=symbol_points,
            histogram_info=histogram_info,
            wave_params=wave_params,
        )

    @classmethod
    def from_info(
        cls,
        graph_type: str,
        curve_info: PlotCurveInfo,
        points: List[Point],
        symbol_points: List[Point],
        histogram_info: Optional[PlotHistogramInfo] = None,
        wave_params: Optional[WaveParams] = None,
    ) -> PlotCurve:
        line_color = pgplot.mpl_color(curve_info["line"]["color"])
        # TODO: line^pattern typo?
        line_style = pgplot.styles[curve_info["line"]["line^pattern"].lower()]
        if curve_info["draw_line"]:
            line_width = curve_info["line"]["width"]
        else:
            line_width = 0.0
        symbol_color = pgplot.mpl_color(curve_info["symbol"]["color"])

        # TODO: symbol^type typo?
        symbol_info = curve_info["symbol"]
        symbol_type = symbol_info["symbol^type"]
        if _should_use_symbol_color(
            symbol_type=symbol_type,
            fill_pattern=symbol_info["fill_pattern"],
        ):
            marker_color = symbol_info["color"]
        else:
            marker_color = "none"

        if curve_info["draw_symbols"] and pgplot.symbols[symbol_type]:
            marker_size = curve_info["symbol"]["height"]
        else:
            marker_size = 0

        # marker
        marker = pgplot.symbols.get(symbol_type, ".")
        # symbol_line_width
        symbol_line_width = curve_info["symbol"]["line_width"]

        xpoints = [p[0] for p in points]
        ypoints = [p[1] for p in points]
        symbol_xs = [p[0] for p in symbol_points]
        symbol_ys = [p[1] for p in symbol_points]
        if symbol_ys:
            y_max = max(
                0.5 * max(max(ypoints), max(symbol_ys)),
                2 * max(max(ypoints), max(symbol_ys)),
            )
            y_min = min(
                0.5 * min(min(ypoints), min(symbol_ys)),
                2 * min(min(ypoints), min(symbol_ys)),
            )
        elif ypoints:
            y_max = max(ypoints)
            y_min = min(ypoints)
        else:
            raise NoCurveDataError("No points found, make sure data is properly initialized")
        # boundaries for wave analysis rectangles

        if xpoints:
            curve_line = PlotCurveLine(
                xs=xpoints,
                ys=ypoints,
                color=line_color,
                linestyle=line_style,
                linewidth=line_width / 2,
            )
        else:
            curve_line = None

        if symbol_xs:
            curve_symbols = PlotCurveSymbols(
                xs=symbol_xs,
                ys=symbol_ys,
                color=symbol_color,
                linewidth=0,
                markerfacecolor=marker_color,
                markersize=marker_size / 2,
                marker=marker,
                markeredgewidth=symbol_line_width / 2,
            )
        else:
            curve_symbols = None

        if graph_type in {"data", "dynamic_aperture", "phase_space"}:
            return cls(
                info=curve_info,
                line=curve_line,
                symbol=curve_symbols,
            )

        if graph_type in {"wave.0", "wave.a", "wave.b"}:
            # Wave region boundaries
            # wave analysis rectangles
            if wave_params is None:
                raise ValueError(f"wave_params required for graph type: {graph_type}")
            if symbol_color in {"blue", "navy", "cyan", "green", "purple"}:
                wave_color = "orange"
            else:
                wave_color = "blue"

            patches = []
            if graph_type in {"wave.0", "wave.a"}:
                a1, a2 = wave_params["ix_a1"], wave_params["ix_a2"]
                patches.append(
                    PlotPatchRectangle(
                        xy=(a1, y_min),
                        width=a2 - a1,
                        height=y_max - y_min,
                        fill=False,
                        color=wave_color,
                    )
                )

            if graph_type in {"wave.0", "wave.b"}:
                b1, b2 = wave_params["ix_b1"], wave_params["ix_b2"]
                patches.append(
                    PlotPatchRectangle(
                        xy=(b1, y_min),
                        width=b2 - b1,
                        height=y_max - y_min,
                        fill=False,
                        color=wave_color,
                    )
                )

            return cls(
                info=curve_info,
                line=curve_line,
                symbol=curve_symbols,
                patches=patches,
            )

        if graph_type == "histogram":
            assert histogram_info is not None
            return cls(
                info=curve_info,
                line=None,
                symbol=None,
                histogram=PlotHistogram(
                    xs=xpoints,
                    bins=histogram_info["number"],
                    weights=ypoints,
                    histtype="step",
                    color=symbol_color,
                ),
            )

        raise NotImplementedError(f"graph_type: {graph_type}")


@dataclasses.dataclass
class PlotBasicGraph:
    info: PlotGraphInfo
    xlim: Point = _point_field
    ylim: Point = _point_field
    xlabel: str = ""
    ylabel: str = ""
    title: str = ""
    show_axes: bool = True
    draw_grid: bool = True
    draw_legend: bool = True
    curves: List[PlotCurve] = Field(default_factory=list)

    @classmethod
    def from_tao(
        cls,
        tao: Tao,
        region_name: str,
        graph_name: str,
        graph_info: Optional[PlotGraphInfo] = None,
    ) -> PlotBasicGraph:
        if graph_info is None:
            graph_info = tao.plot_graph(f"{region_name}.{graph_name}")
            assert graph_info is not None

        graph_type = graph_info["graph^type"]
        if graph_type == "key_table":
            raise NotImplementedError("Key table graphs")

        if graph_type == "lat_layout":
            raise ValueError()
        if graph_type == "floor_plan":
            raise ValueError()
        if graph_info["why_invalid"]:
            raise GraphInvalidError(f"Graph not valid: {graph_info['why_invalid']}")

        all_curve_names = [
            graph_info[f"curve[{i + 1}]"] for i in range(graph_info["num_curves"])
        ]
        curves = []
        for curve_name in all_curve_names:
            try:
                curve = PlotCurve.from_tao(tao, region_name, graph_name, curve_name)
            except NoCurveDataError:
                logger.exception("No curve data?")
            else:
                curves.append(curve)

        return cls(
            info=graph_info,
            curves=curves,
            show_axes=graph_info["draw_axes"],
            title=pgplot.mpl_string("{title} {title_suffix}".format(**graph_info)),
            xlabel=pgplot.mpl_string(graph_info["x_label"]),
            ylabel=pgplot.mpl_string(graph_info["y_label"]),
            draw_grid=graph_info["draw_grid"],
            xlim=(graph_info["x_min"], graph_info["x_max"]),
            ylim=(graph_info["y_min"], graph_info["y_max"]),
            draw_legend=graph_info["draw_curve_legend"],
        )

    def plot(self, ax: Optional[matplotlib.axes.Axes] = None):
        if ax is None:
            _, ax = plt.subplots()
            assert ax is not None

        for curve in self.curves:
            curve.plot(ax)

        # TODO
        # if self.draw_legend:
        #     ax.legend(legend_items, labels)

        if not self.show_axes:
            ax.set_axis_off()

        ax.set_title(self.title)
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.grid(self.draw_grid, which="major", axis="both")
        ax.set_xlim(_fix_limits(self.xlim))
        ax.set_ylim(_fix_limits(self.ylim))
        ax.set_axisbelow(True)
        return ax


@dataclasses.dataclass
class LatticeLayoutElement:
    info: PlotLatLayoutInfo
    patches: List[PlotPatch]
    lines: List[List[Point]]
    annotations: List[PlotAnnotation]
    color: str
    width: float

    def plot(self, ax: matplotlib.axes.Axes):
        ax.add_collection(
            matplotlib.collections.LineCollection(
                self.lines,
                colors=self.color,
                linewidths=self.width,
            )
        )
        for patch in self.patches:
            patch.plot(ax)
        for annotation in self.annotations:
            annotation.plot(ax)

    @classmethod
    def from_info(cls, graph_info: PlotGraphInfo, info: PlotLatLayoutInfo, y2_floor: float):
        s1 = info["ele_s_start"]
        s2 = info["ele_s"]
        y1 = info["y1"]
        y2 = -info["y2"]  # Note negative sign.
        width = info["line_width"]
        color = info["color"]
        shape = info["shape"]
        name = info["label_name"]

        patches = []
        lines = []
        annotations = []

        # Normal case where element is not wrapped around ends of lattice.
        if s2 - s1 > 0:
            # Draw box element
            box_patch = PlotPatchRectangle(
                xy=(s1, y1),
                width=s2 - s1,
                height=y2 - y1,
                linewidth=width,
                color=color,
                fill=False,
            )
            if shape == "box":
                patches.append(box_patch)
            elif shape == "xbox":
                patches.append(box_patch)
                lines.extend([[(s1, y1), (s2, y2)], [(s1, y2), (s2, y1)]])
            elif shape == "x":
                lines.extend([[(s1, y1), (s2, y2)], [(s1, y2), (s2, y1)]])
            elif shape == "bow_tie":
                lines.extend(
                    [
                        [(s1, y1), (s2, y2)],
                        [(s1, y2), (s2, y1)],
                        [(s1, y1), (s1, y2)],
                        [(s2, y1), (s2, y2)],
                    ]
                )
            elif shape == "rbow_tie":
                lines.extend(
                    [
                        [(s1, y1), (s2, y2)],
                        [(s1, y2), (s2, y1)],
                        [(s1, y1), (s2, y1)],
                        [(s1, y2), (s2, y2)],
                    ]
                )
            elif shape == "diamond":
                s_mid = (s1 + s2) / 2
                lines.extend(
                    [
                        [(s1, 0), (s_mid, y1)],
                        [(s1, 0), (s_mid, y2)],
                        [(s2, 0), (s_mid, y1)],
                        [(s2, 0), (s_mid, y2)],
                    ]
                )
            elif shape == "circle":
                s_mid = (s1 + s2) / 2
                patches.append(
                    PlotPatchEllipse(
                        xy=(s_mid, 0),
                        width=y1 - y2,
                        height=y1 - y2,
                        linewidth=width,
                        color=color,
                        fill=False,
                    )
                )

            annotations.append(
                PlotAnnotation(
                    x=(s1 + s2) / 2,
                    y=1.1 * y2_floor,
                    text=name,
                    horizontalalignment="center",
                    verticalalignment="top",
                    clip_on=True,
                    color=color,
                    rotation=90,
                )
            )

        else:
            # Case where element is wrapped round the lattice ends.
            s_min = graph_info["x_min"]
            s_max = graph_info["x_max"]

            for xs, ys in _get_wrapped_shape_coords(
                shape=shape,
                s1=s1,
                s2=s2,
                y1=y1,
                y2=y2,
                s_min=s_min,
                s_max=s_max,
            ):
                lines.append(list(zip(xs, ys)))

            # Draw wrapped element name
            annotations.append(
                PlotAnnotation(
                    x=s_max,
                    y=1.1 * y2_floor,
                    text=name,
                    horizontalalignment="right",
                    verticalalignment="top",
                    clip_on=True,
                    color=color,
                )
            )
            annotations.append(
                PlotAnnotation(
                    x=s_min,
                    y=1.1 * y2_floor,
                    text=name,
                    horizontalalignment="left",
                    verticalalignment="top",
                    clip_on=True,
                    color=color,
                )
            )
        return cls(
            info=info,
            patches=patches,
            lines=lines,
            color=color,
            width=width,
            annotations=annotations,
        )


@dataclasses.dataclass
class PlotLatticeLayoutGraph:
    graph_info: PlotGraphInfo
    elements: List[LatticeLayoutElement]
    xlim: Point
    ylim: Point
    border_xlim: Point
    universe: int
    branch: int
    y2_floor: float

    def plot(self, ax: Optional[matplotlib.axes.Axes] = None):
        if ax is None:
            _, ax = plt.subplots()
        assert ax is not None

        twin_ax = ax.twinx()

        ax.set_axis_off()
        twin_ax.set_axis_off()

        ax.set_navigate(False)
        twin_ax.set_navigate(True)
        ax.axhline(
            y=0,
            xmin=1.1 * self.graph_info["x_min"],
            xmax=1.1 * self.graph_info["x_max"],
            color="Black",
        )

        for elem in self.elements:
            elem.plot(ax)

        # Invisible line to give the lat layout enough vertical space.
        # Without this, the tops and bottoms of shapes could be cut off
        y_max = self.y_max
        ax.plot([0, 0], [-1.7 * y_max, 1.3 * y_max], alpha=0)

        ax.set_xlim(_fix_limits(self.xlim))
        ax.set_ylim(_fix_limits(self.ylim))

    @property
    def y_max(self) -> float:
        ele_y1s = [elem.info["y1"] for elem in self.elements]
        ele_y2s = [elem.info["y2"] for elem in self.elements]
        return max(max(ele_y1s), max(ele_y2s))

    @classmethod
    def from_tao(
        cls,
        tao: Tao,
        region_name: str = "lat_layout",
        graph_name: str = "g",
        branch: Optional[int] = None,
        graph_info: Optional[PlotGraphInfo] = None,
    ) -> PlotLatticeLayoutGraph:
        if graph_info is None:
            graph_info = tao.plot_graph(f"{region_name}.{graph_name}")
            assert graph_info is not None

        graph_type = graph_info["graph^type"]
        if graph_type != "lat_layout":
            raise ValueError(f"Incorrect graph type: {graph_type} for {cls.__name__}")

        universe = 1 if graph_info["ix_universe"] == -1 else graph_info["ix_universe"]
        branch = graph_info["-1^ix_branch"]
        try:
            all_elem_info = tao.plot_lat_layout(ix_uni=universe, ix_branch=branch)
        except RuntimeError as ex:
            if branch != -1:
                raise

            logger.warning(
                f"Lat layout failed for universe={universe} branch={branch}; trying branch 0"
            )
            try:
                all_elem_info = tao.plot_lat_layout(ix_uni=universe, ix_branch=0)
            except RuntimeError:
                print(f"Failed to plot layout: {ex}")
                raise

        all_elem_info = cast(List[PlotLatLayoutInfo], all_elem_info)

        ele_y2s = [info["y2"] for info in all_elem_info]
        y2_floor = -max(ele_y2s)  # Note negative sign

        elements = [
            LatticeLayoutElement.from_info(
                graph_info=graph_info,
                info=info,
                y2_floor=y2_floor,
            )
            for info in all_elem_info
        ]

        return cls(
            graph_info=graph_info,
            xlim=(graph_info["x_min"], graph_info["x_max"]),
            ylim=(graph_info["y_min"], graph_info["y_max"]),
            border_xlim=(1.1 * graph_info["x_min"], 1.1 * graph_info["x_max"]),
            universe=universe,
            branch=branch,
            y2_floor=y2_floor,
            elements=elements,
        )


def _get_wrapped_shape_coords(
    shape: str,
    s1: float,
    s2: float,
    y1: float,
    y2: float,
    s_min: float,
    s_max: float,
):
    """Case where element is wrapped round the lattice ends."""
    if shape == "box":
        return [
            ([s1, s_max], [y1, y1]),
            ([s1, s_max], [y2, y2]),
            ([s_min, s2], [y1, y1]),
            ([s_min, s2], [y2, y2]),
            ([s1, s1], [y1, y2]),
            ([s2, s2], [y1, y2]),
        ]

    if shape == "xbox":
        return [
            ([s1, s_max], [y1, y1]),
            ([s1, s_max], [y2, y2]),
            ([s1, s_max], [y1, 0]),
            ([s1, s_max], [y2, 0]),
            ([s_min, s2], [y1, y1]),
            ([s_min, s2], [y2, y2]),
            ([s_min, s2], [0, y1]),
            ([s_min, s2], [0, y2]),
            ([s1, s1], [y1, y2]),
            ([s2, s2], [y1, y2]),
        ]

    if shape == "x":
        return [
            ([s1, s_max], [y1, 0]),
            ([s1, s_max], [y2, 0]),
            ([s_min, s2], [0, y1]),
            ([s_min, s2], [0, y2]),
        ]

    if shape == "bow_tie":
        return [
            ([s1, s_max], [y1, y1]),
            ([s1, s_max], [y2, y2]),
            ([s1, s_max], [y1, 0]),
            ([s1, s_max], [y2, 0]),
            ([s_min, s2], [y1, y1]),
            ([s_min, s2], [y2, y2]),
            ([s_min, s2], [0, y1]),
            ([s_min, s2], [0, y2]),
        ]

    if shape == "diamond":
        return [
            ([s1, s_max], [0, y1]),
            ([s1, s_max], [0, y2]),
            ([s_min, s2], [y1, 0]),
            ([s_min, s2], [y2, 0]),
        ]

    logger.warning("Unsupported shape: {shape}")
    return []


def _building_wall_to_arc(
    mx,
    my,
    kx,
    ky,
    k_radii,
    color: str,
):
    (c0x, c0y), (c1x, c1y) = util.circle_intersection(
        mx,
        my,
        kx,
        ky,
        abs(k_radii),
    )
    # radius and endpoints specify 2 possible circle centers for arcs
    mpx = (mx + kx) / 2
    mpy = (my + ky) / 2
    if (
        np.arctan2((my - mpy), (mx - mpx))
        < np.arctan2(c0y, c0x)
        < np.arctan2((my - mpy), (mx - mpx))
        and k_radii > 0
    ):
        center = (c1x, c1y)
    elif (
        np.arctan2((my - mpy), (mx - mpx))
        < np.arctan2(c0y, c0x)
        < np.arctan2((my - mpy), (mx - mpx))
        and k_radii < 0
    ):
        center = (c0x, c0y)
    elif k_radii > 0:
        center = (c0x, c0y)
    else:
        center = (c1x, c1y)

    m_angle = 360 + math.degrees(np.arctan2((my - center[1]), (mx - center[0])))
    k_angle = 360 + math.degrees(np.arctan2((ky - center[1]), (kx - center[0])))
    if k_angle > m_angle:
        t1 = m_angle
        t2 = k_angle
    else:
        t1 = k_angle
        t2 = m_angle

    if abs(k_angle - m_angle) > 180:
        t1, t2 = t2, t1

    return PlotPatchArc(
        xy=center,
        width=k_radii * 2,
        height=k_radii * 2,
        theta1=t1,
        theta2=t2,
        color=color,
    )


def _circle_to_patch(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    line_width: float,
    color: str,
):
    return PlotPatchCircle(
        xy=(x1 + (x2 - x1) / 2, y1 + (y2 - y1) / 2),
        radius=off1,
        linewidth=line_width,
        color=color,
        fill=False,
    )


def _box_to_patch(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    off2: float,
    line_width: float,
    color: str,
    angle_start: float,
):
    return PlotPatchRectangle(
        xy=(
            x1 + off2 * np.sin(angle_start),
            y1 - off2 * np.cos(angle_start),
        ),
        width=np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2),
        height=off1 + off2,
        linewidth=line_width,
        color=color,
        fill=False,
        angle=math.degrees(angle_start),
    )


def _create_x_lines(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    off2: float,
    line_width: float,
    color: str,
    angle_start: float,
) -> List[PlotCurveLine]:
    return [
        PlotCurveLine(
            xs=[
                x1 + off2 * np.sin(angle_start),
                x2 - off1 * np.sin(angle_start),
            ],
            ys=[
                y1 - off2 * np.cos(angle_start),
                y2 + off1 * np.cos(angle_start),
            ],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            xs=[
                x1 - off1 * np.sin(angle_start),
                x2 + off2 * np.sin(angle_start),
            ],
            ys=[
                y1 + off1 * np.cos(angle_start),
                y2 - off2 * np.cos(angle_start),
            ],
            linewidth=line_width,
            color=color,
        ),
    ]


def _create_sbend_box(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    off2: float,
    line_width: float,
    color: str,
    angle_start: float,
    angle_end: float,
    rel_angle_start: float,
    rel_angle_end: float,
) -> List[PlotCurveLine]:
    return [
        PlotCurveLine(
            [
                x1 - off1 * np.sin(angle_start - rel_angle_start),
                x1 + off2 * np.sin(angle_start - rel_angle_start),
            ],
            [
                y1 + off1 * np.cos(angle_start - rel_angle_start),
                y1 - off2 * np.cos(angle_start - rel_angle_start),
            ],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            [
                x2 - off1 * np.sin(angle_end + rel_angle_end),
                x2 + off2 * np.sin(angle_end + rel_angle_end),
            ],
            [
                y2 + off1 * np.cos(angle_end + rel_angle_end),
                y2 - off2 * np.cos(angle_end + rel_angle_end),
            ],
            linewidth=line_width,
            color=color,
        ),
    ]


def _create_sbend(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    off2: float,
    line_width: float,
    color: str,
    angle_start: float,
    angle_end: float,
    rel_angle_start: float,
    rel_angle_end: float,
) -> Tuple[List[PlotCurveLine], List[PlotPatch]]:
    line1 = util.line(
        (x1 - off1 * np.sin(angle_start), y1 + off1 * np.cos(angle_start)),
        (x1 + off2 * np.sin(angle_start), y1 - off2 * np.cos(angle_start)),
    )
    line2 = util.line(
        (x2 - off1 * np.sin(angle_end), y2 + off1 * np.cos(angle_end)),
        (x2 + off2 * np.sin(angle_end), y2 - off2 * np.cos(angle_end + rel_angle_end)),
    )
    try:
        intersection = util.intersect(line1, line2)
    except util.NoIntersectionError:
        lines = [
            PlotCurveLine(
                [
                    x1 - off1 * np.sin(angle_start - rel_angle_start),
                    x2 - off1 * np.sin(angle_end + rel_angle_end),
                ],
                [
                    y1 + off1 * np.cos(angle_start - rel_angle_start),
                    y2 + off1 * np.cos(angle_end + rel_angle_end),
                ],
                linewidth=line_width,
                color=color,
            ),
            PlotCurveLine(
                [
                    x1 + off2 * np.sin(angle_start - rel_angle_start),
                    x2 + off2 * np.sin(angle_end + rel_angle_end),
                ],
                [
                    y1 - off2 * np.cos(angle_start - rel_angle_start),
                    y2 - off2 * np.cos(angle_end + rel_angle_end),
                ],
                linewidth=line_width,
                color=color,
            ),
        ]
        return lines, []

    # draw sbend edges if bend angle is 0
    angle1 = 360 + math.degrees(
        np.arctan2(
            y1 + off1 * np.cos(angle_start - rel_angle_start) - intersection[1],
            x1 - off1 * np.sin(angle_start - rel_angle_start) - intersection[0],
        )
    )
    angle2 = 360 + math.degrees(
        np.arctan2(
            y2 + off1 * np.cos(angle_end + rel_angle_end) - intersection[1],
            x2 - off1 * np.sin(angle_end + rel_angle_end) - intersection[0],
        )
    )
    # angles of further curve endpoints relative to center of circle
    angle3 = 360 + math.degrees(
        np.arctan2(
            y1 - off2 * np.cos(angle_start - rel_angle_start) - intersection[1],
            x1 + off2 * np.sin(angle_start - rel_angle_start) - intersection[0],
        )
    )
    angle4 = 360 + math.degrees(
        np.arctan2(
            y2 - off2 * np.cos(angle_end + rel_angle_end) - intersection[1],
            x2 + off2 * np.sin(angle_end + rel_angle_end) - intersection[0],
        )
    )
    # angles of closer curve endpoints relative to center of circle

    if abs(angle1 - angle2) < 180:
        a1 = min(angle1, angle2)
        a2 = max(angle1, angle2)
    else:
        a1 = max(angle1, angle2)
        a2 = min(angle1, angle2)

    if abs(angle3 - angle4) < 180:
        a3 = min(angle3, angle4)
        a4 = max(angle3, angle4)
    else:
        a3 = max(angle3, angle4)
        a4 = min(angle3, angle4)
    # determines correct start and end angles for arcs

    rel_sin = np.sin(angle_start - rel_angle_start)
    rel_cos = np.cos(angle_start - rel_angle_start)
    patches = [
        PlotPatchArc(
            xy=(intersection[0], intersection[1]),
            width=(
                2.0
                * np.sqrt(
                    (x1 - off1 * rel_sin - intersection[0]) ** 2
                    + (y1 + off1 * rel_cos - intersection[1]) ** 2
                )
            ),
            height=(
                2.0
                * np.sqrt(
                    (x1 - off1 * rel_sin - intersection[0]) ** 2
                    + (y1 + off1 * rel_cos - intersection[1]) ** 2
                )
            ),
            theta1=a1,
            theta2=a2,
            linewidth=line_width,
            color=color,
        ),
        PlotPatchArc(
            xy=(intersection[0], intersection[1]),
            width=(
                2.0
                * np.sqrt(
                    (x1 + off2 * rel_sin - intersection[0]) ** 2
                    + (y1 - off2 * rel_cos - intersection[1]) ** 2
                )
            ),
            height=(
                2.0
                * np.sqrt(
                    (x1 + off2 * rel_sin - intersection[0]) ** 2
                    + (y1 - off2 * rel_cos - intersection[1]) ** 2
                )
            ),
            theta1=a3,
            theta2=a4,
            linewidth=line_width,
            color=color,
        ),
    ]
    patch = _sbend_intersection_to_patch(
        intersection=intersection,
        x1=x1,
        x2=x2,
        y1=y1,
        y2=y2,
        off1=off1,
        off2=off2,
        angle_start=angle_start,
        angle_end=angle_end,
        rel_angle_start=rel_angle_start,
        rel_angle_end=rel_angle_end,
    )
    patches.append(patch)
    return [], patches


def _sbend_intersection_to_patch(
    intersection: util.Intersection,
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    off2: float,
    angle_start: float,
    angle_end: float,
    rel_angle_start: float,
    rel_angle_end: float,
):
    sin_start = np.sin(angle_start - rel_angle_start)
    cos_start = np.cos(angle_start - rel_angle_start)
    sin_end = np.sin(angle_end + rel_angle_end)
    cos_end = np.cos(angle_end + rel_angle_end)

    c1 = [x1 - off1 * sin_start, y1 + off1 * cos_start]
    c2 = [x2 - off1 * sin_end, y2 + off1 * cos_end]
    c3 = [x1 + off2 * sin_start, y1 - off2 * cos_start]
    c4 = [x2 + off2 * sin_end, y2 - off2 * cos_end]
    # corners of sbend

    outer_radius = np.sqrt(
        (x1 - off1 * sin_start - intersection[0]) ** 2
        + (y1 + off1 * cos_start - intersection[1]) ** 2
    )
    inner_radius = np.sqrt(
        (x1 + off2 * sin_start - intersection[0]) ** 2
        + (y1 - off2 * cos_start - intersection[1]) ** 2
    )
    if angle_start <= angle_end:
        outer_radius *= -1
        inner_radius *= -1
    # radii of sbend arc edges

    mid_angle = (angle_start + angle_end) / 2

    top = [
        intersection[0] - outer_radius * np.sin(mid_angle),
        intersection[1] + outer_radius * np.cos(mid_angle),
    ]
    bottom = [
        intersection[0] - inner_radius * np.sin(mid_angle),
        intersection[1] + inner_radius * np.cos(mid_angle),
    ]
    # midpoints of top and bottom arcs in an sbend

    top_cp = [
        2 * (top[0]) - 0.5 * (c1[0]) - 0.5 * (c2[0]),
        2 * (top[1]) - 0.5 * (c1[1]) - 0.5 * (c2[1]),
    ]
    bottom_cp = [
        2 * (bottom[0]) - 0.5 * (c3[0]) - 0.5 * (c4[0]),
        2 * (bottom[1]) - 0.5 * (c3[1]) - 0.5 * (c4[1]),
    ]
    # corresponding control points for a quadratic Bezier curve that passes through the corners and arc midpoint

    verts = [c1, top_cp, c2, c4, bottom_cp, c3, c1]
    codes: List[CustomPathCommand] = [
        "MOVETO",
        "CURVE3",
        "CURVE3",
        "LINETO",
        "CURVE3",
        "CURVE3",
        "CLOSEPOLY",
    ]
    return PlotPatchCustom(
        vertices=verts,
        commands=codes,
        facecolor="green",
        alpha=0.5,
    )


def _create_bow_tie(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    off2: float,
    line_width: float,
    color: str,
    angle_start: float,
):
    return [
        PlotCurveLine(
            [
                x1 + off2 * np.sin(angle_start),
                x2 - off1 * np.sin(angle_start),
            ],
            [
                y1 - off2 * np.cos(angle_start),
                y2 + off1 * np.cos(angle_start),
            ],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            [
                x1 - off1 * np.sin(angle_start),
                x2 + off2 * np.sin(angle_start),
            ],
            [
                y1 + off1 * np.cos(angle_start),
                y2 - off2 * np.cos(angle_start),
            ],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            [
                x1 - off1 * np.sin(angle_start),
                x2 - off1 * np.sin(angle_start),
            ],
            [
                y1 + off1 * np.cos(angle_start),
                y2 + off1 * np.cos(angle_start),
            ],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            [
                x1 + off2 * np.sin(angle_start),
                x2 + off2 * np.sin(angle_start),
            ],
            [
                y1 - off2 * np.cos(angle_start),
                y2 - off2 * np.cos(angle_start),
            ],
            linewidth=line_width,
            color=color,
        ),
    ]


def _create_diamond(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    off1: float,
    off2: float,
    line_width: float,
    color: str,
    angle_start: float,
):
    return [
        PlotCurveLine(
            [x1, x1 + (x2 - x1) / 2 - off1 * np.sin(angle_start)],
            [y1, y1 + (y2 - y1) / 2 + off1 * np.cos(angle_start)],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            [x1 + (x2 - x1) / 2 - off1 * np.sin(angle_start), x2],
            [y1 + (y2 - y1) / 2 + off1 * np.cos(angle_start), y2],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            [x1, x1 + (x2 - x1) / 2 + off2 * np.sin(angle_start)],
            [y1, y1 + (y2 - y1) / 2 - off2 * np.cos(angle_start)],
            linewidth=line_width,
            color=color,
        ),
        PlotCurveLine(
            [x1 + (x2 - x1) / 2 + off2 * np.sin(angle_start), x2],
            [y1 + (y2 - y1) / 2 - off2 * np.cos(angle_start), y2],
            linewidth=line_width,
            color=color,
        ),
    ]


@dataclasses.dataclass
class FloorPlanElement:
    branch_index: int
    index: int
    info: FloorPlanElementInfo
    lines: List[PlotCurveLine]
    patches: List[PlotPatch]
    annotations: List[PlotAnnotation]

    def plot(self, ax: matplotlib.axes.Axes):
        for line in self.lines:
            line.plot(ax)
        for patch in self.patches:
            patch.plot(ax)
        for annotation in self.annotations:
            annotation.plot(ax)

    @classmethod
    def from_info(cls, info: FloorPlanElementInfo):
        # Handle some renaming and reduce dictionary key usage
        return cls._from_info(
            info,
            branch_index=info["branch_index"],
            index=info["index"],
            ele_key=info["ele_key"],
            x1=info["end1_r1"],
            y1=info["end1_r2"],
            angle_start=info["end1_theta"],
            x2=info["end2_r1"],
            y2=info["end2_r2"],
            angle_end=info["end2_theta"],
            line_width=info["line_width"],
            shape=info["shape"],
            off1=info["y1"],
            off2=info["y2"],
            color=info["color"],
            label_name=info["label_name"],
            # ele_l=info["ele_l"],
            # ele_angle=info["ele_angle"],
            rel_angle_start=info.get("ele_e1", 0.0),
            rel_angle_end=info.get("ele_e", 0.0),
        )

    @classmethod
    def _from_info(
        cls,
        info: FloorPlanElementInfo,
        *,
        branch_index: int,
        index: int,
        ele_key: str,
        x1: float,
        y1: float,
        angle_start: float,
        x2: float,
        y2: float,
        angle_end: float,
        line_width: float,
        shape: str,
        off1: float,
        off2: float,
        color: str,
        label_name: str,
        # Only for sbend:
        rel_angle_start: float = 0.0,
        rel_angle_end: float = 0.0,
    ) -> FloorPlanElement:
        ele_key = ele_key.lower()

        lines: List[PlotCurveLine] = []
        patches: List[PlotPatch] = []
        annotations: List[PlotAnnotation] = []

        if ele_key == "drift" or ele_key == "kicker":
            # draw drift element
            lines.append(PlotCurveLine(xs=[x1, x2], ys=[y1, y2], color="black"))

        if off1 == 0 and off2 == 0 and ele_key != "sbend" and color:
            # draw line element
            lines.append(
                PlotCurveLine(xs=[x1, x2], ys=[y1, y2], linewidth=line_width, color=color)
            )

        elif shape == "box" and ele_key != "sbend" and color:
            patches.append(
                _box_to_patch(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    off2=off2,
                    line_width=line_width,
                    color=color,
                    angle_start=angle_start,
                )
            )

        elif shape == "xbox" and ele_key != "sbend" and color:
            patches.append(
                _box_to_patch(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    off2=off2,
                    line_width=line_width,
                    color=color,
                    angle_start=angle_start,
                )
            )
            lines.extend(
                _create_x_lines(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    off2=off2,
                    line_width=line_width,
                    color=color,
                    angle_start=angle_start,
                )
            )

        elif shape == "x" and ele_key != "sbend" and color:
            lines.extend(
                _create_x_lines(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    off2=off2,
                    line_width=line_width,
                    color=color,
                    angle_start=angle_start,
                )
            )

        elif shape == "bow_tie" and ele_key != "sbend" and color:
            lines.extend(
                _create_bow_tie(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    off2=off2,
                    line_width=line_width,
                    color=color,
                    angle_start=angle_start,
                )
            )
        elif shape == "diamond" and ele_key != "sbend" and color:
            lines.extend(
                _create_diamond(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    off2=off2,
                    line_width=line_width,
                    color=color,
                    angle_start=angle_start,
                )
            )

        elif shape == "circle" and ele_key != "sbend" and color:
            patches.append(
                _circle_to_patch(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    line_width=line_width,
                    color=color,
                )
            )

        elif shape == "box" and ele_key == "sbend" and color:
            # draws straight sbend edges
            lines.extend(
                _create_sbend_box(
                    x1=x1,
                    x2=x2,
                    y1=y1,
                    y2=y2,
                    off1=off1,
                    off2=off2,
                    line_width=line_width,
                    color=color,
                    angle_start=angle_start,
                    angle_end=angle_end,
                    rel_angle_start=rel_angle_start,
                    rel_angle_end=rel_angle_end,
                )
            )
            sbend_lines, sbend_patches = _create_sbend(
                x1=x1,
                x2=x2,
                y1=y1,
                y2=y2,
                off1=off1,
                off2=off2,
                line_width=line_width,
                color=color,
                angle_start=angle_start,
                angle_end=angle_end,
                rel_angle_start=rel_angle_start,
                rel_angle_end=rel_angle_end,
            )
            lines.extend(sbend_lines or [])
            patches.extend(sbend_patches or [])

        if label_name and color and np.sin(((angle_end + angle_start) / 2)) > 0:
            annotations.append(
                PlotAnnotation(
                    x=x1 + (x2 - x1) / 2 - 1.3 * off1 * np.sin(angle_start),
                    y=y1 + (y2 - y1) / 2 + 1.3 * off1 * np.cos(angle_start),
                    text=label_name,
                    horizontalalignment="right",
                    verticalalignment="center",
                    color="black",
                    clip_on=True,
                    rotation=-90 + math.degrees((angle_end + angle_start) / 2),
                    rotation_mode="anchor",
                )
            )

        elif label_name and color and np.sin(((angle_end + angle_start) / 2)) <= 0:
            annotations.append(
                PlotAnnotation(
                    x=x1 + (x2 - x1) / 2 - 1.3 * off1 * np.sin(angle_start),
                    y=y1 + (y2 - y1) / 2 + 1.3 * off1 * np.cos(angle_start),
                    text=label_name,
                    horizontalalignment="left",
                    verticalalignment="center",
                    color="black",
                    rotation=90 + math.degrees((angle_end + angle_start) / 2),
                    clip_on=True,
                    rotation_mode="anchor",
                )
            )

        return cls(
            branch_index=branch_index,
            index=index,
            info=info,
            lines=lines,
            patches=patches,
            annotations=annotations,
        )
        # path approximating sbend region for clickable region on graph using lines and quadratic Bezier curves

        # else:  # for non sbend click detection
        #     corner1[str(i)] = [
        #         x1 - off1 * np.sin(angle_start),
        #         y1 + off1 * np.cos(angle_start),
        #     ]
        #     corner2[str(i)] = [
        #         x2 - off1 * np.sin(angle_start),
        #         y2 + off1 * np.cos(angle_start),
        #     ]
        #     corner3[str(i)] = [
        #         x1 + off2 * np.sin(angle_start),
        #         y1 - off2 * np.cos(angle_start),
        #     ]
        #     corner4[str(i)] = [
        #         x2 + off2 * np.sin(angle_start),
        #         y2 - off2 * np.cos(angle_start),
        #     ]
        # coordinates of corners of a floor plan element for clickable region


@dataclasses.dataclass
class BuildingWalls:
    building_wall_graph: List[BuildingWallGraphInfo]
    lines: List[PlotCurveLine]
    patches: List[PlotPatch]

    def plot(self, ax: matplotlib.axes.Axes):
        for line in self.lines:
            line.plot(ax)
        for patch in self.patches:
            patch.plot(ax)

    @classmethod
    def from_info(
        cls,
        building_wall_graph: List[BuildingWallGraphInfo],
        wall_list: List[BuildingWallInfo],
        elem_to_color: Dict[str, str],
    ) -> BuildingWalls:
        building_wall_curves = set(graph["index"] for graph in building_wall_graph)
        building_wall_types = {wall["index"]: wall["name"] for wall in wall_list}
        lines = []
        patches = []
        for curve_name in sorted(building_wall_curves):
            points = []  # index of point in curve
            xs = []  # list of point x coordinates
            ys = []  # list of point y coordinates
            radii = []  # straight line if element has 0 or missing radius
            for bwg in building_wall_graph:
                if curve_name == bwg["index"]:
                    points.append(bwg["point"])
                    xs.append(bwg["offset_x"])
                    ys.append(bwg["offset_y"])
                    radii.append(bwg["radius"])

            for k in range(max(points), 1, -1):
                idx_k = points.index(k)
                idx_m = points.index(k - 1)  # adjacent point to connect to
                if building_wall_types[curve_name] not in elem_to_color:
                    # (original todo message included)
                    # TODO: This is a temporary fix to deal with building wall
                    # segments that don't have an associated graph_info shape
                    # Currently this will fail to match to wild cards in the
                    # shape name (e.g. building_wall::* should match to every
                    # building wall segment, but currently it matches to none).
                    # A more sophisticated way of getting the graph_info shape
                    # settings for building walls will be required in the
                    # future, either through a python command in tao or with a
                    # method on the python to match wild cards to wall segment
                    # names
                    logger.warning(
                        f"No graph_info shape defined for building_wall segment "
                        f"{building_wall_types[curve_name]}"
                    )
                    continue

                color = elem_to_color[building_wall_types[curve_name]]
                if radii[idx_k] == 0:  # draw building wall line
                    lines.append(
                        PlotCurveLine(
                            xs=[xs[idx_k], xs[idx_m]],
                            ys=[ys[idx_k], ys[idx_m]],
                            color=color,
                        )
                    )

                else:  # draw building wall arc
                    patches.append(
                        _building_wall_to_arc(
                            mx=xs[idx_m],
                            my=ys[idx_m],
                            kx=xs[idx_k],
                            ky=ys[idx_k],
                            k_radii=radii[idx_k],
                            color=color,
                        )
                    )

        # plot floor plan building walls
        return cls(building_wall_graph=building_wall_graph, lines=lines, patches=patches)


@dataclasses.dataclass
class FloorOrbits:
    info: List[FloorOrbitInfo]
    line: PlotCurveLine

    @classmethod
    def from_tao(
        cls,
        tao: Tao,
        region_name: str,
        graph_name: str,
        color: str,
    ) -> FloorOrbits:
        floor_orbit_info = cast(
            List[FloorOrbitInfo],
            tao.floor_orbit(f"{region_name}.{graph_name}"),
        )

        xs = []
        ys = []
        for info in floor_orbit_info:
            if info["ele_key"] == "x":
                xs.extend(info["orbits"])
            elif info["ele_key"] == "y":
                ys.extend(info["orbits"])

        return cls(
            info=floor_orbit_info,
            line=PlotCurveLine(
                xs=xs,
                ys=ys,
                color=color,
            ),
        )

    def plot(self, ax: matplotlib.axes.Axes):
        self.line.plot(ax)


@dataclasses.dataclass
class FloorPlanGraph:
    info: PlotGraphInfo
    building_walls: BuildingWalls
    floor_orbits: Optional[FloorOrbits]
    elements: List[FloorPlanElement] = Field(default_factory=list)
    xlim: Point = _point_field
    ylim: Point = _point_field
    xlabel: str = ""
    ylabel: str = ""
    title: str = ""
    show_axes: bool = False
    draw_grid: bool = False
    draw_legend: bool = False

    @classmethod
    def from_tao(
        cls,
        tao: Tao,
        region_name: str,
        graph_name: str,
        graph_info: Optional[PlotGraphInfo] = None,
    ) -> FloorPlanGraph:
        full_name = f"{region_name}.{graph_name}"
        if graph_info is None:
            graph_info = tao.plot_graph(full_name)
            assert graph_info is not None

        graph_type = graph_info["graph^type"]
        if graph_type != "floor_plan":
            raise ValueError(f"Incorrect graph type: {graph_type} for {cls.__name__}")

        elem_infos = cast(
            List[FloorPlanElementInfo],
            tao.floor_plan(f"{region_name}.{graph_name}"),
        )
        elements = [FloorPlanElement.from_info(info) for info in elem_infos]
        elem_to_color = {
            elem["ele_id"].split(":")[0]: pgplot.mpl_color(elem["color"])
            for elem in tao.shape_list("floor_plan")
        }

        building_walls = BuildingWalls.from_info(
            building_wall_graph=cast(
                List[BuildingWallGraphInfo],
                tao.building_wall_graph(full_name),
            ),
            wall_list=cast(List[BuildingWallInfo], tao.building_wall_list()),
            elem_to_color=elem_to_color,
        )
        floor_orbits = None
        if float(graph_info["floor_plan_orbit_scale"]) != 0:
            floor_orbits = FloorOrbits.from_tao(
                tao,
                region_name=region_name,
                graph_name=graph_name,
                color=graph_info["floor_plan_orbit_color"].lower(),
            )

        return cls(
            info=graph_info,
            elements=elements,
            building_walls=building_walls,
            floor_orbits=floor_orbits,
            title=pgplot.mpl_string("{title} {title_suffix}".format(**graph_info)),
            xlabel=pgplot.mpl_string(graph_info["x_label"]),
            ylabel=pgplot.mpl_string(graph_info["y_label"]),
            draw_grid=graph_info["draw_grid"],
            xlim=(graph_info["x_min"], graph_info["x_max"]),
            ylim=(graph_info["y_min"], graph_info["y_max"]),
            draw_legend=graph_info["draw_curve_legend"],
        )

    def plot(self, ax: Optional[matplotlib.axes.Axes] = None):
        if ax is None:
            _, ax = plt.subplots()
            assert ax is not None

        for elem in self.elements:
            elem.plot(ax)

        self.building_walls.plot(ax)
        if self.floor_orbits is not None:
            self.floor_orbits.plot(ax)

        if not self.show_axes:
            ax.set_axis_off()

        ax.set_title(self.title)
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.grid(self.draw_grid, which="major", axis="both")
        ax.set_xlim(_fix_limits(self.xlim))
        ax.set_ylim(_fix_limits(self.ylim))
        ax.set_axisbelow(True)
        return ax


def get_graphs_in_region(tao: Tao, region_name: str):
    plot1_info = tao.plot1(region_name)

    if "num_graphs" not in plot1_info:
        raise RuntimeError("Plotting disabled?")

    return [plot1_info[f"graph[{i + 1}]"] for i in range(plot1_info["num_graphs"])]


def make_graph(
    tao: Tao,
    region_name: str,
    graph_name: str,
):
    graph_info = cast(PlotGraphInfo, tao.plot_graph(f"{region_name}.{graph_name}"))
    graph_type = graph_info["graph^type"]

    logger.debug(f"Creating graph {region_name}.{graph_name} ({graph_type})")

    if graph_type == "floor_plan":
        return FloorPlanGraph.from_tao(
            tao=tao,
            region_name=region_name,
            graph_name=graph_name,
            graph_info=graph_info,
        )
    if graph_type == "lat_layout":
        return PlotLatticeLayoutGraph.from_tao(
            tao,
            region_name=region_name,
            graph_name=graph_name,
            graph_info=graph_info,
        )
    return PlotBasicGraph.from_tao(
        tao,
        region_name=region_name,
        graph_name=graph_name,
        graph_info=graph_info,
    )


def plot_graph(
    tao: Tao,
    region_name: str,
    graph_name: str,
    ax: Optional[matplotlib.axes.Axes] = None,
):
    graph = make_graph(tao, region_name, graph_name)

    if ax is None:
        _, ax = plt.subplots()
        assert ax is not None

    graph.plot(ax)
    return ax, graph


def plot_region(tao: Tao, region_name: str):
    fig = plt.figure()

    graph_names = get_graphs_in_region(tao, region_name=region_name)

    if not len(graph_names):
        return

    # gs = fig.add_gridspec(nrows=number_graphs, ncols=1, height_ratios=graph_heights)
    gs = fig.subplots(nrows=len(graph_names), ncols=1, sharex=True, squeeze=False)

    for ax, graph_name in zip(gs[:, 0], graph_names):
        plot_graph(
            tao=tao,
            region_name=region_name,
            graph_name=graph_name,
            ax=ax,
        )
