import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import asyncio


@dataclass
class ProfileMetric:
    """Represents a single performance metric."""
    component: str
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self) -> float:
        """Mark the metric as finished and calculate duration."""
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        return self.duration


@dataclass
class ProfileSummary:
    """Summary of all profiling metrics for a request."""
    total_duration: float
    metrics: List[ProfileMetric]
    
    def get_component_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary grouped by component."""
        summary = {}
        for metric in self.metrics:
            if metric.component not in summary:
                summary[metric.component] = {
                    'total_time': 0.0,
                    'operations': {}
                }
            
            if metric.duration:
                summary[metric.component]['total_time'] += metric.duration
                summary[metric.component]['operations'][metric.operation] = metric.duration
                
        return summary
    
    def generate_timeline(self, width: int = 80) -> str:
        """Generate a visual timeline showing when each component was active (excluding VAD)."""
        if not self.metrics or self.total_duration <= 0:
            return "No timeline data available"
        
        # Filter out VAD operations from timeline visualization
        non_vad_metrics = [metric for metric in self.metrics if metric.component != 'vad']
        
        if not non_vad_metrics:
            return "No timeline data available (VAD operations excluded)"
        
        # Find the earliest start time to normalize all times (excluding VAD)
        earliest_start = min(metric.start_time for metric in non_vad_metrics if metric.start_time)
        
        # Create timeline data structure (excluding VAD operations)
        timeline_data = []
        for metric in non_vad_metrics:
            if metric.start_time and metric.end_time and metric.duration:
                relative_start = metric.start_time - earliest_start
                relative_end = metric.end_time - earliest_start
                timeline_data.append({
                    'component': metric.component,
                    'operation': metric.operation,
                    'start': relative_start,
                    'end': relative_end,
                    'duration': metric.duration
                })
        
        # Sort by start time
        timeline_data.sort(key=lambda x: x['start'])
        
        lines = []
        lines.append("📈 EXECUTION TIMELINE")
        lines.append("=" * width)
        
        # Create time scale
        time_scale = self._create_time_scale(width - 20)
        lines.append(f"Time:     {time_scale}")
        lines.append("")
        
        # Create visual bars for each operation
        for item in timeline_data:
            bar = self._create_timeline_bar(item, width - 20)
            component_label = f"{item['component'][:8]:8s}"
            lines.append(f"{component_label}: {bar} ({item['duration']:.3f}s)")
        
        lines.append("")
        lines.append("Legend: █ = Active execution time")
        lines.append("")
        
        return "\n".join(lines)
    
    def _create_time_scale(self, width: int) -> str:
        """Create a time scale for the timeline."""
        if self.total_duration <= 0:
            return "0" + " " * (width - 1)
        
        scale = []
        for i in range(width):
            time_point = (i / (width - 1)) * self.total_duration
            if i == 0:
                scale.append("0")
            elif i == width - 1:
                scale.append(f"{self.total_duration:.1f}s")
            elif i % (width // 4) == 0:  # Show markers at 25%, 50%, 75%
                scale.append(f"{time_point:.1f}")
            else:
                scale.append(" ")
        
        return "".join(scale)
    
    def _create_timeline_bar(self, item: Dict, width: int) -> str:
        """Create a visual bar representing the execution time of an operation."""
        if self.total_duration <= 0:
            return "█" * width
        
        # Calculate start and end positions
        start_pos = int((item['start'] / self.total_duration) * width)
        end_pos = int((item['end'] / self.total_duration) * width)
        
        # Ensure minimum width of 1 character
        if end_pos <= start_pos:
            end_pos = start_pos + 1
        
        # Create the bar
        bar = [" "] * width
        for i in range(start_pos, min(end_pos, width)):
            bar[i] = "█"
        
        return "".join(bar)
    
    def detect_concurrency(self) -> List[Dict[str, Any]]:
        """Detect overlapping operations that indicate concurrency (excluding VAD)."""
        if not self.metrics:
            return []
        
        # Filter out VAD operations from concurrency analysis
        non_vad_metrics = [metric for metric in self.metrics if metric.component != 'vad']
        
        if not non_vad_metrics:
            return []
        
        # Find the earliest start time to normalize (excluding VAD)
        earliest_start = min(metric.start_time for metric in non_vad_metrics if metric.start_time)
        
        # Create normalized timeline events (excluding VAD operations)
        events = []
        for metric in non_vad_metrics:
            if metric.start_time and metric.end_time:
                events.append({
                    'type': 'start',
                    'time': metric.start_time - earliest_start,
                    'component': metric.component,
                    'operation': metric.operation,
                    'metric': metric
                })
                events.append({
                    'type': 'end',
                    'time': metric.end_time - earliest_start,
                    'component': metric.component,
                    'operation': metric.operation,
                    'metric': metric
                })
        
        # Sort events by time
        events.sort(key=lambda x: x['time'])
        
        # Detect overlaps
        active_operations = []
        overlaps = []
        
        for event in events:
            if event['type'] == 'start':
                # Check for overlaps with currently active operations
                for active in active_operations:
                    overlaps.append({
                        'operation1': f"{active['component']}.{active['operation']}",
                        'operation2': f"{event['component']}.{event['operation']}",
                        'overlap_start': event['time'],
                        'overlap_duration': min(active['end_time'], event['metric'].end_time - earliest_start) - event['time']
                    })
                
                active_operations.append({
                    'component': event['component'],
                    'operation': event['operation'],
                    'end_time': event['metric'].end_time - earliest_start
                })
            else:  # end event
                # Remove from active operations
                active_operations = [op for op in active_operations 
                                   if not (op['component'] == event['component'] and 
                                          op['operation'] == event['operation'])]
        
        return overlaps
    
    def format_summary(self) -> str:
        """Format the profiling summary as a readable string."""
        lines = []
        lines.append("=" * 80)
        lines.append("🔍 PERFORMANCE PROFILING SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Total Request Duration: {self.total_duration:.3f}s")
        lines.append("")
        
        # Add timeline visualization
        timeline = self.generate_timeline(80)
        lines.append(timeline)
        lines.append("")
        
        component_summary = self.get_component_summary()
        
        # Calculate total sequential time (sum of all component times)
        total_component_time = sum(data['total_time'] for data in component_summary.values())
        
        # Sort components by total time (descending)
        sorted_components = sorted(
            component_summary.items(), 
            key=lambda x: x[1]['total_time'], 
            reverse=True
        )
        
        lines.append("📊 COMPONENT BREAKDOWN")
        lines.append("-" * 40)
        
        for component, data in sorted_components:
            lines.append(f"🔧 {component.upper()}")
            
            # Calculate percentage based on total component time to ensure they add up to 100%
            # Also show the ratio to actual request duration for concurrency indication
            component_percentage = (data['total_time'] / total_component_time) * 100 if total_component_time > 0 else 0
            concurrency_ratio = data['total_time'] / self.total_duration if self.total_duration > 0 else 0
            
            if concurrency_ratio > 1.1:  # If significantly longer than request duration, show concurrency info
                lines.append(f"   Total Time: {data['total_time']:.3f}s ({component_percentage:.1f}% of total work, {concurrency_ratio:.1f}x concurrent)")
            else:
                lines.append(f"   Total Time: {data['total_time']:.3f}s ({component_percentage:.1f}%)")
            
            # Sort operations by duration (descending)
            sorted_ops = sorted(data['operations'].items(), key=lambda x: x[1], reverse=True)
            for operation, duration in sorted_ops:
                lines.append(f"   └─ {operation}: {duration:.3f}s")
            lines.append("")
        
        # Add concurrency analysis
        overlaps = self.detect_concurrency()
        if overlaps:
            lines.append("🔄 CONCURRENCY ANALYSIS")
            lines.append("-" * 40)
            for overlap in overlaps:
                if overlap['overlap_duration'] > 0.001:  # Only show significant overlaps
                    lines.append(f"⚡ Concurrent execution detected:")
                    lines.append(f"   {overlap['operation1']} ⟷ {overlap['operation2']}")
                    lines.append(f"   Overlap duration: {overlap['overlap_duration']:.3f}s")
                    lines.append("")
        
        # Add summary statistics
        if total_component_time > self.total_duration * 1.1:
            concurrency_factor = total_component_time / self.total_duration
            lines.append("💡 PERFORMANCE INSIGHTS")
            lines.append("-" * 40)
            lines.append(f"🚀 Concurrency Factor: {concurrency_factor:.1f}x (operations ran in parallel)")
            lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


class PerformanceProfilerService:
    """Service for tracking performance metrics across application components."""
    
    def __init__(self):
        self._current_metrics: List[ProfileMetric] = []
        self._request_start_time: Optional[float] = None
        self._is_profiling: bool = False
    
    def start_request_profiling(self) -> None:
        """Start profiling for a new request."""
        self._current_metrics.clear()
        self._request_start_time = time.perf_counter()
        self._is_profiling = True
    
    def stop_request_profiling(self) -> ProfileSummary:
        """Stop profiling and return summary."""
        if not self._is_profiling or self._request_start_time is None:
            return ProfileSummary(total_duration=0.0, metrics=[])
        
        total_duration = time.perf_counter() - self._request_start_time
        self._is_profiling = False
        
        return ProfileSummary(
            total_duration=total_duration,
            metrics=self._current_metrics.copy()
        )
    
    def start_metric(self, component: str, operation: str, metadata: Optional[Dict[str, Any]] = None) -> ProfileMetric:
        """Start tracking a new metric."""
        if not self._is_profiling:
            # Return a dummy metric if not profiling
            return ProfileMetric(
                component=component,
                operation=operation,
                start_time=time.perf_counter(),
                metadata=metadata or {}
            )
        
        metric = ProfileMetric(
            component=component,
            operation=operation,
            start_time=time.perf_counter(),
            metadata=metadata or {}
        )
        
        self._current_metrics.append(metric)
        return metric
    
    def finish_metric(self, metric: ProfileMetric) -> float:
        """Finish tracking a metric and return its duration."""
        return metric.finish()
    
    @asynccontextmanager
    async def profile_async(self, component: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Async context manager for profiling operations."""
        metric = self.start_metric(component, operation, metadata)
        try:
            yield metric
        finally:
            self.finish_metric(metric)
    
    def profile_sync(self, component: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Synchronous context manager for profiling operations."""
        class SyncProfileContext:
            def __init__(self, profiler: PerformanceProfilerService, comp: str, op: str, meta: Optional[Dict[str, Any]]):
                self.profiler = profiler
                self.component = comp
                self.operation = op
                self.metadata = meta
                self.metric = None
            
            def __enter__(self):
                self.metric = self.profiler.start_metric(self.component, self.operation, self.metadata)
                return self.metric
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.metric:
                    self.profiler.finish_metric(self.metric)
        
        return SyncProfileContext(self, component, operation, metadata)
    
    def is_profiling_active(self) -> bool:
        """Check if profiling is currently active."""
        return self._is_profiling
    
    def get_current_metrics_count(self) -> int:
        """Get the number of metrics collected so far."""
        return len(self._current_metrics)