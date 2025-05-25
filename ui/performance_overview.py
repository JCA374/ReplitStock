"""
Performance overview component for displaying scanner performance metrics
"""
import logging
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def display_performance_metrics(metrics: Optional[Dict[str, Any]] = None):
    """
    Display scanner performance metrics in a Streamlit UI
    
    Args:
        metrics: Dictionary containing performance metrics.
                If None, it will try to get metrics from session state
    """
    if metrics is None:
        # Try to get metrics from session state
        metrics = st.session_state.get('performance_metrics', None)
        
    if not metrics:
        st.info("No performance data available for this scan.")
        return
        
    st.subheader("🚀 Performance Overview")
    
    # Top level metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_duration = metrics.get('total_duration_seconds', 0)
        st.metric("Total Scan Time", f"{total_duration:.2f}s")
        
    with col2:
        error_count = metrics.get('error_count', 0)
        st.metric("Errors", error_count)
        
    with col3:
        operation_count = sum(metrics.get('operation_counts', {}).values())
        st.metric("Operations", operation_count)
    
    # Performance breakdown
    if 'operation_timings' in metrics and metrics['operation_timings']:
        st.subheader("⏱️ Operation Timing Breakdown")
        
        # Create DataFrame for operations
        timings = metrics['operation_timings']
        timing_df = pd.DataFrame({
            'Operation': list(timings.keys()),
            'Time (seconds)': list(timings.values())
        })
        
        # Sort by time
        timing_df = timing_df.sort_values('Time (seconds)', ascending=False)
        
        # Add percentage
        total_time = timing_df['Time (seconds)'].sum()
        timing_df['Percentage'] = (timing_df['Time (seconds)'] / total_time * 100).round(1)
        timing_df['Percentage'] = timing_df['Percentage'].apply(lambda x: f"{x}%")
        
        # Display as bar chart
        fig = go.Figure(go.Bar(
            x=timing_df['Time (seconds)'],
            y=timing_df['Operation'],
            orientation='h',
            marker_color='royalblue'
        ))
        
        fig.update_layout(
            title="Operation Timing (seconds)",
            xaxis_title="Time (seconds)",
            yaxis_title="Operation",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show detailed table
        with st.expander("View Detailed Timing Data", expanded=False):
            st.dataframe(timing_df)
    
    # Database and API statistics
    if 'database_stats' in metrics:
        st.subheader("📊 Database Performance")
        db_stats = metrics['database_stats']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Database Queries", db_stats.get('query_count', 0))
            st.metric("Cache Hits", db_stats.get('cache_hit_count', 0))
            
        with col2:
            st.metric("DB Query Time", f"{db_stats.get('query_time', 0):.2f}s")
            st.metric("Cache Hit Rate", f"{db_stats.get('cache_hit_rate', 0):.1f}%")
    
    # API statistics
    if 'api_stats' in metrics:
        st.subheader("🌐 API Performance")
        api_stats = metrics['api_stats']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("API Calls", api_stats.get('call_count', 0))
            st.metric("Failed Calls", api_stats.get('failed_calls', 0))
            
        with col2:
            st.metric("API Time", f"{api_stats.get('total_time', 0):.2f}s")
            st.metric("Average Call Time", f"{api_stats.get('avg_call_time', 0):.2f}s")
            
    # Memory usage
    if 'memory_usage' in metrics:
        st.subheader("💾 Memory Usage")
        memory = metrics['memory_usage']
        
        # Format peak memory
        peak_mb = memory.get('peak_mb', 0)
        st.metric("Peak Memory Usage", f"{peak_mb:.1f} MB")
        
        # Memory chart if history available
        if 'history' in memory:
            memory_history = memory['history']
            memory_df = pd.DataFrame(memory_history)
            
            fig = go.Figure(go.Scatter(
                x=memory_df['timestamp'],
                y=memory_df['usage_mb'],
                mode='lines+markers',
                marker=dict(size=6),
                line=dict(width=2)
            ))
            
            fig.update_layout(
                title="Memory Usage Over Time",
                xaxis_title="Time",
                yaxis_title="Memory Usage (MB)",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Error details
    if 'errors' in metrics and metrics['errors']:
        st.subheader("❌ Error Details")
        
        errors = metrics['errors']
        error_df = pd.DataFrame(errors)
        
        st.dataframe(error_df, use_container_width=True)