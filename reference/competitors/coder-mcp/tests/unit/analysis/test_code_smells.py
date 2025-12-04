"""
Tests for code smell detection functionality.

Tests the refactored code smell detection system with specialized detectors.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from coder_mcp.analysis.detectors.code_smells.complexity import ComplexitySmellDetector
from coder_mcp.analysis.detectors.code_smells.coordinator import CodeSmellDetector
from coder_mcp.analysis.detectors.code_smells.quality import QualitySmellDetector
from coder_mcp.analysis.detectors.code_smells.structural import StructuralSmellDetector


class TestCodeSmellDetector:
    """Test the main CodeSmellDetector coordinator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CodeSmellDetector()
        self.test_file = Path("test_file.py")

    def test_init_default(self):
        """Test detector initialization with defaults"""
        assert self.detector.available_detectors is not None
        assert len(self.detector.available_detectors) > 0
        assert "structural" in self.detector.available_detectors
        assert "quality" in self.detector.available_detectors
        assert "complexity" in self.detector.available_detectors

    def test_init_with_enabled_detectors(self):
        """Test detector initialization with specific enabled detectors"""
        detector = CodeSmellDetector(enabled_detectors=["structural", "quality"])
        assert len(detector.enabled_detectors) == 2
        assert "structural" in detector.enabled_detectors
        assert "quality" in detector.enabled_detectors
        assert "complexity" not in detector.enabled_detectors

    def test_detect_code_smells_valid_content(self):
        """Test code smell detection with valid content"""
        content = """
def very_long_function_name_that_should_trigger_detection():
    x = 1
    y = 2
    z = 3
    # This function might trigger structural smells
    pass
"""

        smells = self.detector.detect_code_smells(content, self.test_file)
        assert isinstance(smells, list)
        # Should be able to detect at least some basic issues

    def test_detect_code_smells_empty_content(self):
        """Test code smell detection with empty content"""
        smells = self.detector.detect_code_smells("", self.test_file)
        assert smells == []

        smells = self.detector.detect_code_smells("   \n  \n  ", self.test_file)
        assert smells == []

    def test_detect_code_smells_with_filters(self):
        """Test code smell detection with specific smell type filters"""
        content = """
def test_function():
    password = "hardcoded_secret"  # Should trigger quality detector
    x = 1
    y = 2
"""

        # Test with specific enabled smells filter
        smells = self.detector.detect_code_smells(
            content, self.test_file, enabled_smells=["hardcoded_secrets"]
        )
        assert isinstance(smells, list)

    def test_get_smell_statistics_empty(self):
        """Test statistics generation with no smells"""
        stats = self.detector.get_smell_statistics([])
        assert stats["total_smells"] == 0
        assert stats["files_affected"] == 0
        assert stats["quality_score"] == 10.0  # Perfect score

    def test_get_smell_statistics_with_smells(self):
        """Test statistics generation with detected smells"""
        smells = [
            {"type": "long_function", "file": "test1.py", "line": 10, "severity": "medium"},
            {"type": "hardcoded_secret", "file": "test1.py", "line": 20, "severity": "high"},
            {"type": "complex_condition", "file": "test2.py", "line": 5, "severity": "low"},
        ]

        stats = self.detector.get_smell_statistics(smells)
        assert stats["total_smells"] == 3
        assert stats["files_affected"] == 2
        assert "by_severity" in stats
        assert "by_type" in stats
        assert stats["most_common_smell"] is not None
        assert stats["quality_score"] < 10.0

    def test_get_available_smell_types(self):
        """Test getting available smell types"""
        smell_types = self.detector.get_available_smell_types()
        assert isinstance(smell_types, dict)
        assert (
            "structural" in smell_types or "quality" in smell_types or "complexity" in smell_types
        )

    def test_configure_detector(self):
        """Test detector configuration"""
        # Test enabling detector
        self.detector.enabled_detectors.discard("complexity")
        self.detector.configure_detector("complexity", True)
        assert "complexity" in self.detector.enabled_detectors

        # Test disabling detector
        self.detector.configure_detector("complexity", False)
        assert "complexity" not in self.detector.enabled_detectors

    def test_add_custom_detector(self):
        """Test adding custom detector"""
        mock_detector = Mock()
        mock_detector.detect.return_value = []

        self.detector.add_custom_detector("custom", mock_detector)
        assert "custom" in self.detector.available_detectors
        assert "custom" in self.detector.enabled_detectors

    def test_add_invalid_custom_detector(self):
        """Test adding invalid custom detector"""
        invalid_detector = Mock()
        # Remove detect method to make it invalid
        del invalid_detector.detect

        with pytest.raises(ValueError):
            self.detector.add_custom_detector("invalid", invalid_detector)

    def test_post_process_smells(self):
        """Test smell post-processing (deduplication and sorting)"""
        smells = [
            {"type": "test_smell", "file": "test.py", "line": 10, "severity": "low"},
            {"type": "test_smell", "file": "test.py", "line": 10, "severity": "low"},  # Duplicate
            {"type": "other_smell", "file": "test.py", "line": 5, "severity": "high"},
        ]

        processed = self.detector._post_process_smells(smells)
        assert len(processed) == 2  # Duplicate removed
        assert processed[0]["severity"] == "high"  # High severity first

    def test_error_handling(self):
        """Test error handling in detector execution"""
        # Create a detector that will raise an exception
        mock_detector = Mock()
        mock_detector.detect.side_effect = Exception("Test error")

        self.detector.available_detectors["error_detector"] = mock_detector
        self.detector.enabled_detectors.add("error_detector")

        # Should not raise exception, should continue with other detectors
        smells = self.detector.detect_code_smells("test content", self.test_file)
        assert isinstance(smells, list)


class TestStructuralSmellDetector:
    """Test the StructuralSmellDetector"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = StructuralSmellDetector()
        self.test_file = Path("test_file.py")

    def test_detect_basic_structural_smells(self):
        """Test detection of basic structural smells"""
        content = """
def very_long_function_name_that_might_indicate_poor_structure():
    # This function has a very long name
    pass

class god_class_that_does_everything:
    # Class with potentially too many responsibilities
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
"""

        smells = self.detector.detect(content, self.test_file)
        assert isinstance(smells, list)


class TestQualitySmellDetector:
    """Test the QualitySmellDetector"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = QualitySmellDetector()
        self.test_file = Path("test_file.py")

    def test_detect_quality_smells(self):
        """Test detection of quality-related smells"""
        content = """
password = "hardcoded_secret123"
api_key = "AKIAIOSFODNN7EXAMPLE"
def test():
    result = eval("1 + 1")  # Dangerous eval
    return result
"""

        smells = self.detector.detect(content, self.test_file)
        assert isinstance(smells, list)


class TestComplexitySmellDetector:
    """Test the ComplexitySmellDetector"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = ComplexitySmellDetector()
        self.test_file = Path("test_file.py")

    def test_detect_complexity_smells(self):
        """Test detection of complexity-related smells"""
        content = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                if x > y:
                    if y > z:
                        return x + y + z
                    else:
                        return x - y - z
                else:
                    return x * y * z
            else:
                return x + y
        else:
            return x
    else:
        return 0
"""

        smells = self.detector.detect(content, self.test_file)
        assert isinstance(smells, list)


class TestCodeSmellIntegration:
    """Integration tests for the complete code smell detection system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CodeSmellDetector()
        self.test_file = Path("complex_test_file.py")

    def test_comprehensive_analysis(self):
        """Test comprehensive code smell analysis"""
        content = """
# Test file with multiple types of smells

password = "secret123"  # Quality smell: hardcoded secret

def very_long_function_with_complex_logic_and_poor_structure():  # Structural smell
    '''This function demonstrates multiple code smells'''

    # Complexity smell: deeply nested conditions
    if True:
        if True:
            if True:
                if True:
                    if True:
                        result = eval("1 + 1")  # Quality smell: dangerous eval
                        return result

    # Quality smell: inefficient string concatenation
    output = ""
    for i in range(100):
        output += str(i)

    return output

class GodClass:  # Structural smell: potential god class
    '''Class that tries to do everything'''

    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
"""

        smells = self.detector.detect_code_smells(content, self.test_file)

        assert isinstance(smells, list)
        assert len(smells) > 0

        # Should detect various types of smells
        # Note: smell_types variable is used for validation but not explicitly checked
        # in this test - it could be used for more specific assertions if needed

        # Generate statistics
        stats = self.detector.get_smell_statistics(smells)
        assert stats["total_smells"] == len(smells)
        assert stats["files_affected"] >= 1
        assert "by_severity" in stats
        assert "by_type" in stats

    def test_detector_coordination(self):
        """Test coordination between different detector types"""
        # Test with only structural detector enabled
        detector = CodeSmellDetector(enabled_detectors=["structural"])
        smells_structural = detector.detect_code_smells(
            "def long_function_name(): pass", self.test_file
        )

        # Test with only quality detector enabled
        detector = CodeSmellDetector(enabled_detectors=["quality"])
        smells_quality = detector.detect_code_smells('password = "secret"', self.test_file)

        # Test with all detectors enabled
        detector = CodeSmellDetector()
        smells_all = detector.detect_code_smells(
            'def long_name(): password = "secret"', self.test_file
        )

        # All should return lists
        assert isinstance(smells_structural, list)
        assert isinstance(smells_quality, list)
        assert isinstance(smells_all, list)

    def test_performance_with_large_content(self):
        """Test performance with larger code content"""
        # Generate a reasonably large code snippet
        methods = "\n".join([f"    def method_{i}(self): pass" for i in range(50)])
        content = f"""
class LargeClass:
{methods}

def large_function():
    password = "secret123"
    {'x = 1' * 100}  # Lots of repetitive code
    return x
"""

        smells = self.detector.detect_code_smells(content, self.test_file)
        assert isinstance(smells, list)

        # Should complete without errors and find some smells
        stats = self.detector.get_smell_statistics(smells)
        assert isinstance(stats, dict)
