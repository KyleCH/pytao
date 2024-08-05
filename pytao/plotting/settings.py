from typing import Dict, List, Optional, Tuple, Union
from typing_extensions import Literal

import pydantic


tao_colors = frozenset(
    {
        "Not_Set",
        "White",
        "Black",
        "Red",
        "Green",
        "Blue",
        "Cyan",
        "Magenta",
        "Yellow",
        "Orange",
        "Yellow_Green",
        "Light_Green",
        "Navy_Blue",
        "Purple",
        "Reddish_Purple",
        "Dark_Grey",
        "Light_Grey",
        "Transparent",
    }
)


class QuickPlotPoint(pydantic.BaseModel):
    x: float = pydantic.Field(kw_only=False)
    y: float = pydantic.Field(kw_only=False)
    units: str = pydantic.Field(max_length=16, default=" ", kw_only=False)

    def get_commands(
        self,
        region_name: str,
        graph_name: str,
        parent_name: str,
    ) -> List[str]:
        return [
            f"set graph {region_name}.{graph_name} {parent_name}%{key} = {value}"
            for key, value in self.model_dump().items()
            if value is not None
        ]


QuickPlotPointTuple = Tuple[float, float, str]


class QuickPlotRectangle(pydantic.BaseModel):
    x1: float = pydantic.Field(kw_only=False)
    x2: float = pydantic.Field(kw_only=False)
    y1: float = pydantic.Field(kw_only=False)
    y2: float = pydantic.Field(kw_only=False)
    units: str = pydantic.Field(default=" ", max_length=16)

    def get_commands(
        self,
        region_name: str,
        graph_name: str,
        parent_name: str,
    ) -> List[str]:
        return [
            f"set graph {region_name}.{graph_name} {parent_name}%{key} = {value}"
            for key, value in self.model_dump().items()
            if value is not None
        ]


QuickPlotRectangleTuple = Tuple[float, float, float, float, str]


class TaoAxisSettings(pydantic.BaseModel):
    bounds: Optional[Literal["zero_at_end", "zero_symmetric", "general", "exact"]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    number_offset: Optional[float] = None
    label_offset: Optional[float] = None
    major_tick_len: Optional[float] = None
    minor_tick_len: Optional[float] = None
    label_color: Optional[str] = pydantic.Field(max_length=16)
    major_div: Optional[int] = None
    major_div_nominal: Optional[int] = None
    minor_div: Optional[int] = None
    minor_div_max: Optional[int] = None
    places: Optional[int] = None
    tick_side: Optional[int] = None
    number_side: Optional[int] = None
    label: Optional[str] = pydantic.Field(max_length=80)
    type: Optional[Literal["log", "linear"]] = None
    draw_label: Optional[bool] = None
    draw_numbers: Optional[bool] = None

    def get_commands(
        self,
        region_name: str,
        axis_name: str,
    ) -> List[str]:
        return [
            f"set graph {region_name} {axis_name}%{key} = {value}"
            for key, value in self.model_dump().items()
            if value is not None
        ]


class TaoFloorPlanSettings(pydantic.BaseModel):
    correct_distortion: Optional[bool] = None
    size_is_absolute: Optional[bool] = None
    draw_only_first_pass: Optional[bool] = None
    flip_label_side: Optional[bool] = None
    rotation: Optional[float] = None
    orbit_scale: Optional[float] = None
    orbit_color: Optional[float] = None
    orbit_lattice: Optional[float] = None
    orbit_pattern: Optional[float] = None
    orbit_width: Optional[int] = None
    view: Optional[Literal["xy", "xz", "yx", "yz", "zx", "zy"]] = None

    def get_commands(
        self,
        region_name: str,
        graph_name: str,
    ) -> List[str]:
        return [
            f"set graph {region_name}.{graph_name} floor_plan%{key} = {value}"
            for key, value in self.model_dump().items()
            if value is not None
        ]


class TaoGraphSettings(pydantic.BaseModel):
    text_legend: Dict[int, str] = pydantic.Field(default_factory=dict)
    allow_wrap_around: Optional[bool] = None
    box: Dict[int, int] = pydantic.Field(
        default_factory=dict,
        description="Defines which box the plot is put in.",
    )
    component: Optional[str] = None
    clip: Optional[bool] = None
    curve_legend_origin: Optional[Union[QuickPlotPoint, QuickPlotPointTuple]] = None
    draw_axes: Optional[bool] = None
    draw_title: Optional[bool] = None
    draw_curve_legend: Optional[bool] = None
    draw_grid: Optional[bool] = None
    draw_only_good_user_data_or_vars: Optional[bool] = None
    floor_plan: Optional[TaoFloorPlanSettings] = None
    ix_universe: Optional[int] = None
    ix_branch: Optional[int] = None
    margin: Optional[Union[QuickPlotRectangle, QuickPlotRectangleTuple]] = None
    name: Optional[str] = None
    scale_margin: Optional[Union[QuickPlotRectangle, QuickPlotRectangleTuple]] = None
    symbol_size_scale: Optional[float] = None
    text_legend_origin: Optional[Union[QuickPlotRectangle, QuickPlotRectangleTuple]] = None
    title: Optional[str] = None
    type: Optional[str] = None
    x: Optional[TaoAxisSettings] = None
    x2: Optional[TaoAxisSettings] = None
    y: Optional[TaoAxisSettings] = None
    y2: Optional[TaoAxisSettings] = None
    y2_mirrors_y: Optional[bool] = None
    x_axis_scale_factor: Optional[float] = None

    def get_commands(
        self,
        region_name: str,
        graph_name: str,
        graph_type: str,
    ) -> List[str]:
        result = []
        for key in self.model_dump().keys():
            value = getattr(self, key)
            if value is None:
                continue

            if key in ("curve_legend_origin",) and isinstance(value, tuple):
                value = QuickPlotPoint(*value)
            elif key in ("scale_margin", "margin", "text_legend_origin") and isinstance(
                value, tuple
            ):
                value = QuickPlotRectangle(*value)

            if isinstance(value, QuickPlotPoint):
                result.extend(value.get_commands(region_name, graph_name, key))
            elif isinstance(value, TaoFloorPlanSettings):
                result.extend(value.get_commands(region_name, graph_name))
            elif isinstance(value, QuickPlotRectangle):
                result.extend(value.get_commands(region_name, graph_name, key))
            elif isinstance(value, TaoAxisSettings):
                result.extend(value.get_commands(region_name, key))
            elif key == "text_legend":
                for legend_index, legend_value in value.items():
                    result.append(
                        f"set graph {region_name}.{graph_name} text_legend({legend_index}) = {legend_value}"
                    )
            elif key == "box":
                for box_index, box_value in value.items():
                    result.append(
                        f"set graph {region_name}.{graph_name} box({box_index}) = {box_value}"
                    )
            elif isinstance(value, TaoFloorPlanSettings):
                if graph_type == "floor_plan":
                    result.extend(value.get_commands(region_name, graph_name))
            else:
                result.append(f"set graph {region_name}.{graph_name} {key} = {value}")
        return result
