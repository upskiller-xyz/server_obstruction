"""Obstruction angle visualization utility

Stateless utility class for visualizing obstruction angles from obstruction_all endpoint.
Follows OOP principles and design patterns from CLAUDE.md.
"""
from typing import List, Dict, Any, Tuple
from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes


class PlotConfig(Enum):
    """Configuration constants for plot appearance"""
    MAX_ANGLE_DEGREES = 90.0
    BAR_COLOR = 'black'
    FIGURE_WIDTH = 12.0
    FIGURE_HEIGHT = 6.0
    DEFAULT_DPI = 150
    BAR_WIDTH = 0.8
    GRID_ALPHA = 0.3
    LINE_ALPHA = 0.7
    TEXT_ALPHA = 0.6
    LINE_WIDTH = 0.5
    TEXT_FONT_SIZE = 9


class AngleType(Enum):
    """Types of obstruction angles"""
    HORIZON = 'horizon'
    ZENITH = 'zenith'


class ResponseField(Enum):
    """Field names in API responses"""
    DIRECTION_ANGLE = 'direction_angle'
    HORIZON = 'horizon'
    ZENITH = 'zenith'
    OBSTRUCTION_ANGLE_DEGREES = 'obstruction_angle_degrees'
    RESULTS = 'results'
    DATA = 'data'


class AxisLabel(Enum):
    """Axis labels and titles"""
    X_LABEL = 'Direction Index'
    Y_LABEL = 'Obstruction Angle (degrees)'
    TITLE = 'Obstruction Angles by Direction'
    HORIZON_TEXT = 'Horizon →'
    ZENITH_TEXT = '← Zenith'


class ResponseAdapter:
    """
    Adapter Pattern: Convert API responses to standard format

    Handles both /obstruction_all and /obstruction response formats
    """

    @classmethod
    def adapt(cls, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert API response to standard list format

        Args:
            response_data: Response from /obstruction_all or /obstruction endpoint

        Returns:
            List of result dictionaries in standard format

        Raises:
            ValueError: If response format is invalid
        """
        # Check if it's obstruction_all format with nested data.results
        if ResponseField.DATA.value in response_data:
            data = response_data[ResponseField.DATA.value]

            # Check for data.results (obstruction_all format)
            if ResponseField.RESULTS.value in data:
                return data[ResponseField.RESULTS.value]

            # Check for data.horizon/data.zenith (obstruction format)
            if ResponseField.HORIZON.value in data and ResponseField.ZENITH.value in data:
                return [{
                    ResponseField.DIRECTION_ANGLE.value: 0.0,
                    ResponseField.HORIZON.value: data[ResponseField.HORIZON.value],
                    ResponseField.ZENITH.value: data[ResponseField.ZENITH.value]
                }]

        # Check if it's obstruction_all format (has 'results' key at top level)
        if ResponseField.RESULTS.value in response_data:
            return response_data[ResponseField.RESULTS.value]

        # If response_data is already a list, assume it's in correct format
        if isinstance(response_data, list):
            return response_data

        raise ValueError(
            "Invalid response format. Expected 'results' or 'data' field in response, "
            "or a list of result dictionaries."
        )


class IAngleExtractor(ABC):
    """Abstract interface for extracting angles from results"""

    @abstractmethod
    def extract(self, results: List[Dict[str, Any]]) -> List[float]:
        """Extract angles from results"""
        pass


class HorizonAngleExtractor(IAngleExtractor):
    """Extract horizon obstruction angles from results"""

    def extract(self, results: List[Dict[str, Any]]) -> List[float]:
        """Extract horizon angles from results"""
        return [
            result[ResponseField.HORIZON.value][ResponseField.OBSTRUCTION_ANGLE_DEGREES.value]
            for result in results
        ]


class ZenithAngleExtractor(IAngleExtractor):
    """Extract zenith obstruction angles from results"""

    def extract(self, results: List[Dict[str, Any]]) -> List[float]:
        """Extract zenith angles from results"""
        return [
            result[ResponseField.ZENITH.value][ResponseField.OBSTRUCTION_ANGLE_DEGREES.value]
            for result in results
        ]


class IBarPlotter(ABC):
    """Abstract interface for plotting obstruction bars"""

    @abstractmethod
    def plot(self, ax: Axes, x_positions: np.ndarray, angles: List[float]) -> None:
        """Plot bars on axes"""
        pass


class HorizonBarPlotter(IBarPlotter):
    """Plot horizon obstruction bars (growing upward from bottom)"""

    def plot(self, ax: Axes, x_positions: np.ndarray, angles: List[float]) -> None:
        """Plot horizon bars growing upward from 0"""
        ax.bar(
            x_positions,
            angles,
            color=PlotConfig.BAR_COLOR.value,
            label=AngleType.HORIZON.value.capitalize(),
            width=PlotConfig.BAR_WIDTH.value
        )


class ZenithBarPlotter(IBarPlotter):
    """Plot zenith obstruction bars (growing downward from top)"""

    def plot(self, ax: Axes, x_positions: np.ndarray, angles: List[float]) -> None:
        """Plot zenith bars growing downward from 90 degrees"""
        ax.bar(
            x_positions,
            angles,
            bottom=PlotConfig.MAX_ANGLE_DEGREES.value,
            color=PlotConfig.BAR_COLOR.value,
            label=AngleType.ZENITH.value.capitalize(),
            width=PlotConfig.BAR_WIDTH.value
        )


class PlotConfigurer:
    """Configure plot appearance and labels (Single Responsibility)"""

    @classmethod
    def configure(cls, ax: Axes, num_results: int) -> None:
        """
        Configure plot appearance and labels

        Args:
            ax: Matplotlib axes
            num_results: Number of direction results
        """
        cls._set_axis_limits(ax, num_results)
        cls._add_boundary_line(ax)
        cls._set_labels(ax)
        cls._configure_y_axis(ax)
        cls._add_grid(ax)
        cls._add_legend(ax)

    @classmethod
    def _set_axis_limits(cls, ax: Axes, num_results: int) -> None:
        """Set X and Y axis limits"""
        ax.set_ylim(0, PlotConfig.MAX_ANGLE_DEGREES.value * 2)
        ax.set_xlim(-0.5, num_results - 0.5)

    @classmethod
    def _add_boundary_line(cls, ax: Axes) -> None:
        """Add horizontal line at 90 degrees (horizon/zenith boundary)"""
        ax.axhline(
            y=PlotConfig.MAX_ANGLE_DEGREES.value,
            color='gray',
            linestyle='--',
            linewidth=PlotConfig.LINE_WIDTH.value,
            alpha=PlotConfig.LINE_ALPHA.value
        )

    @classmethod
    def _set_labels(cls, ax: Axes) -> None:
        """Set axis labels and title"""
        ax.set_xlabel(AxisLabel.X_LABEL.value)
        ax.set_ylabel(AxisLabel.Y_LABEL.value)
        ax.set_title(AxisLabel.TITLE.value)

    @classmethod
    def _configure_y_axis(cls, ax: Axes) -> None:
        """Configure Y-axis to show angles from bottom (horizon) and top (zenith)"""
        tick_positions = [0, 30, 60, 90, 120, 150, 180]
        tick_labels = ['0°', '30°', '60°', '90°', '60°', '30°', '0°']

        ax.set_yticks(tick_positions)
        ax.set_yticklabels(tick_labels)

        cls._add_axis_annotations(ax)

    @classmethod
    def _add_axis_annotations(cls, ax: Axes) -> None:
        """Add text annotations for horizon and zenith sides"""
        ax.text(
            -0.5, 45, AxisLabel.HORIZON_TEXT.value,
            rotation=90,
            verticalalignment='center',
            fontsize=PlotConfig.TEXT_FONT_SIZE.value,
            alpha=PlotConfig.TEXT_ALPHA.value
        )
        ax.text(
            -0.5, 135, AxisLabel.ZENITH_TEXT.value,
            rotation=90,
            verticalalignment='center',
            fontsize=PlotConfig.TEXT_FONT_SIZE.value,
            alpha=PlotConfig.TEXT_ALPHA.value
        )

    @classmethod
    def _add_grid(cls, ax: Axes) -> None:
        """Add grid to plot"""
        ax.grid(True, alpha=PlotConfig.GRID_ALPHA.value, axis='y')

    @classmethod
    def _add_legend(cls, ax: Axes) -> None:
        """Add legend to plot"""
        ax.legend()


class ObstructionVisualizer:
    """
    Stateless utility class for visualizing obstruction angles as bar plots

    Follows OOP principles from CLAUDE.md:
    - Single Responsibility: Only orchestrates visualization
    - Strategy Pattern: Uses extractors and plotters for different angle types
    - Enumerator Pattern: All constants defined as enums
    - Stateless: All methods are classmethods
    - Dependency Injection: Uses composition of specialized classes
    """

    # Strategy Pattern: Map angle types to extractors
    _ANGLE_EXTRACTORS = {
        AngleType.HORIZON: HorizonAngleExtractor(),
        AngleType.ZENITH: ZenithAngleExtractor()
    }

    # Strategy Pattern: Map angle types to plotters
    _BAR_PLOTTERS = {
        AngleType.HORIZON: HorizonBarPlotter(),
        AngleType.ZENITH: ZenithBarPlotter()
    }

    @classmethod
    def make(
        cls,
        response_data: Dict[str, Any],
        figsize: Tuple[float, float] = None
    ) -> None:
        """
        Create and display a bar plot visualization of obstruction angles

        Args:
            response_data: API response from /obstruction_all or /obstruction endpoint
                          Supports multiple formats:
                          - {'results': [...]} from /obstruction_all
                          - {'data': {'horizon': {...}, 'zenith': {...}}} from /obstruction
                          - List of result dictionaries directly
            figsize: Optional figure size (width, height)

        Example:
            >>> # From /obstruction_all
            >>> response = {'results': [{'direction_angle': 0.0, ...}, ...]}
            >>> ObstructionVisualizer.make(response)

            >>> # From /obstruction
            >>> response = {'data': {'horizon': {...}, 'zenith': {...}}}
            >>> ObstructionVisualizer.make(response)
        """
        # Adapter Pattern: Convert response to standard format
        results = ResponseAdapter.adapt(response_data)

        figsize = cls._get_figsize(figsize)

        # Extract data using Strategy Pattern
        horizon_angles = cls._extract_angles(results, AngleType.HORIZON)
        zenith_angles = cls._extract_angles(results, AngleType.ZENITH)
        x_positions = np.arange(len(results))

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Plot bars using Strategy Pattern
        cls._plot_bars(ax, x_positions, horizon_angles, AngleType.HORIZON)
        cls._plot_bars(ax, x_positions, zenith_angles, AngleType.ZENITH)

        # Configure plot
        PlotConfigurer.configure(ax, len(results))

        plt.tight_layout()
        plt.show()

    @classmethod
    def _get_figsize(cls, figsize: Tuple[float, float] = None) -> Tuple[float, float]:
        """Get figure size, using default if not provided"""
        if figsize is None:
            return (PlotConfig.FIGURE_WIDTH.value, PlotConfig.FIGURE_HEIGHT.value)
        return figsize

    @classmethod
    def _extract_angles(cls, results: List[Dict[str, Any]], angle_type: AngleType) -> List[float]:
        """
        Extract angles using Strategy Pattern

        Args:
            results: Result dictionaries
            angle_type: Type of angle to extract

        Returns:
            List of angles in degrees
        """
        extractor = cls._ANGLE_EXTRACTORS[angle_type]
        return extractor.extract(results)

    @classmethod
    def _plot_bars(
        cls,
        ax: Axes,
        x_positions: np.ndarray,
        angles: List[float],
        angle_type: AngleType
    ) -> None:
        """
        Plot bars using Strategy Pattern

        Args:
            ax: Matplotlib axes
            x_positions: X positions for bars
            angles: Angles in degrees
            angle_type: Type of angle to plot
        """
        plotter = cls._BAR_PLOTTERS[angle_type]
        plotter.plot(ax, x_positions, angles)

