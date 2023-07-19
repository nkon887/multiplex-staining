import unittest

from multiplex.helpertools import correct_path


class TestCorrectPath(unittest.TestCase):
    def test_list_str(self):
        """
        Test that it can correct a path string
        """
        data = r"dir\subdir\filename"
        result = correct_path(data)
        self.assertEqual(result, "dir/subdir/filename")


if __name__ == '__main__':
    unittest.main()
