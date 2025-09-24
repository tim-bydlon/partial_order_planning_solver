"""
Test configuration and fixtures for pytest
"""

import pytest
import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_robot_start_state():
    """Standard robot starting state for tests"""
    return ['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']


@pytest.fixture
def sample_paint_ceiling_goal():
    """Standard goal to paint ceiling"""
    return ['Painted(Ceiling)']


@pytest.fixture
def sample_paint_both_goal():
    """Goal to paint both ceiling and ladder"""
    return ['Painted(Ceiling)', 'Painted(Ladder)']