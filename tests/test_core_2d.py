import pytest
from core import Core, Point2D

def test_point_to_index_basic():
    """Test basic 2D to 1D conversion"""
    core = Core(size=100, width=10)  # 10x10 grid
    assert core.point_to_index(Point2D(0, 0)) == 0
    assert core.point_to_index(Point2D(1, 0)) == 1
    assert core.point_to_index(Point2D(2, 0)) == 2
    assert core.point_to_index(Point2D(0, 1)) == 10
    assert core.point_to_index(Point2D(0, 2)) == 20
    assert core.point_to_index(Point2D(3, 4)) == 43
    assert core.point_to_index(Point2D(9, 9)) == 99

def test_point_to_index_wrapping():
    """Test wrapping behavior within rows and columns"""
    core = Core(size=100, width=10)
    
    # Test x wrapping within row
    assert core.point_to_index(Point2D(10, 0)) == 10  # wraps to start of row
    assert core.point_to_index(Point2D(11, 0)) == 11
    assert core.point_to_index(Point2D(-1, 0)) == 99  # wraps to end of row
    
    # Test y wrapping
    assert core.point_to_index(Point2D(0, 1)) == 10  
    assert core.point_to_index(Point2D(0, 10)) == 1  # wraps to start of next column
    assert core.point_to_index(Point2D(0, 11)) == 11 # wraps to second pos of second column
    assert core.point_to_index(Point2D(0, -1)) == 99  # wraps to start of last column

def test_point_to_index_overflow():
    """Test handling of overflow between rows"""
    core = Core(size=100, width=10)
    
    # Test x overflow to next row
    assert core.point_to_index(Point2D(10, 0)) == 10  # wraps to start of next row
    assert core.point_to_index(Point2D(20, 0)) == 20  # wraps to start of next row
    
    # Test x overflow with negative values
    assert core.point_to_index(Point2D(-1, 0)) == 99  # wraps to end of previous row
    assert core.point_to_index(Point2D(-11, 0)) == 89  # wraps to end of previous row

def test_point_to_index_negative():
    """Test handling of negative coordinates"""
    core = Core(size=100, width=10)
    
    # Test negative x values
    assert core.point_to_index(Point2D(-1, 0)) == 99
    assert core.point_to_index(Point2D(-10, 0)) == 90
    assert core.point_to_index(Point2D(-11, 0)) == 89
    
    # Test negative y values
    assert core.point_to_index(Point2D(0, -1)) == 99
    assert core.point_to_index(Point2D(0, -10)) == 9
    assert core.point_to_index(Point2D(0, -11)) == 98
    
    # Test both negative
    assert core.point_to_index(Point2D(-1, -1)) == 88
    assert core.point_to_index(Point2D(-11, -11)) == 77


def test_point_to_index_edge_cases():
    """Test edge cases and boundary conditions"""
    core = Core(size=100, width=10)
    
    # Test at grid boundaries
    assert core.point_to_index(Point2D(9, 0)) == 9  # end of first row
    assert core.point_to_index(Point2D(0, 9)) == 90  # start of last row
    assert core.point_to_index(Point2D(9, 9)) == 99  # last cell
    
    # Test wrapping at boundaries
    assert core.point_to_index(Point2D(10, 0)) == 10  # wraps to start of next row
    assert core.point_to_index(Point2D(0, 10)) == 1  # wraps to start of next column
    
    # Test large numbers
    assert core.point_to_index(Point2D(100, 0)) == 0
    assert core.point_to_index(Point2D(0, 100)) == 0
    assert core.point_to_index(Point2D(100, 100)) == 0

def test_point_to_index_invalid_width():
    """Test error handling for invalid width"""
    with pytest.raises(ValueError):
        Core(size=100, width=7)  # 100 not divisible by 7 


def test_point_to_grid():
    core = Core(size=6, width=3)
    
    # Test trim with positive values
    assert core.point_to_grid(Point2D(3, 0)) == Point2D(0, 1)  # Wraps to next row
    assert core.point_to_grid(Point2D(0, 2)) == Point2D(1, 0)  # Wraps to start
    
    # Test trim with negative values
    assert core.point_to_grid(Point2D(-1, 0)) == Point2D(2, 1)  # Wraps to previous row
    assert core.point_to_grid(Point2D(0, -1)) == Point2D(2, 1)  # Wraps to previous column
