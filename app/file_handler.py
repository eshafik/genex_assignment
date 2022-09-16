import os
import glob
from pathlib import PosixPath
from typing import List, Union


__all__ = ['FileHandler']


class FileHandler:
    """File parser class for collecting files from specific directory or file path"""
    def __init__(self, file_path: Union[PosixPath, bool], file_extension: str):
        self.file_path = file_path
        self.file_ext = file_extension

    @staticmethod
    def file_exists(file_path: Union[PosixPath, str]) -> bool:
        """Check file path exists or not"""
        return os.path.exists(file_path)

    def get_file(self) -> Union[str, None]:
        """Collect a single file from file path"""
        if self.file_path.name.split('.')[-1] == 'eml':
            return str(self.file_path)
        raise ValueError(f'No valid {self.file_ext} file found!')

    def get_files(self) -> List[str]:
        """Get multiple files from a specific file path/directory"""
        files_path = f'{self.file_path}/*{self.file_ext}'
        return glob.glob(files_path)

    def file_list(self) -> List[str]:
        """Get list of exact files associated with the provided file extension"""
        if not self.file_exists(self.file_path):
            raise ValueError('No valid file path found!')
        if os.path.isdir(self.file_path):
            return self.get_files()
        return [self.get_file()]
