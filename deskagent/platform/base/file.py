from abc import ABC, abstractmethod


class FileInformation(ABC):
    @abstractmethod
    def get_info(self, path):
        pass

    @abstractmethod
    def get_metadata(self, path):
        pass

    @abstractmethod
    def get_size(self, path):
        pass

    @abstractmethod
    def get_type(self, path):
        pass

    @abstractmethod
    def get_extension(self, path):
        pass

    @abstractmethod
    def get_mime_type(self, path):
        pass

    @abstractmethod
    def get_absolute_path(self, path):
        pass

    @abstractmethod
    def get_name(self, path):
        pass

    @abstractmethod
    def get_directory(self, path):
        pass

    @abstractmethod
    def get_created_at(self, path):
        pass

    @abstractmethod
    def get_modified_at(self, path):
        pass

    @abstractmethod
    def get_accessed_at(self, path):
        pass

    @abstractmethod
    def is_file(self, path):
        pass

    @abstractmethod
    def is_directory(self, path):
        pass

    @abstractmethod
    def is_symlink(self, path):
        pass

    @abstractmethod
    def get_access_permissions(self, path):
        pass


class FileLifecycle(ABC):
    @abstractmethod
    def create(self, path, content=""):
        pass

    @abstractmethod
    def delete(self, path):
        pass

    @abstractmethod
    def restore(self, path):
        pass

    @abstractmethod
    def move_to_trash(self, path):
        pass

    @abstractmethod
    def empty_trash(self):
        pass

    @abstractmethod
    def rename(self, path, new_name):
        pass

    @abstractmethod
    def copy(self, source, destination):
        pass

    @abstractmethod
    def move(self, source, destination):
        pass

    @abstractmethod
    def duplicate(self, path):
        pass

    @abstractmethod
    def replace(self, target, source):
        pass


class FileContent(ABC):
    @abstractmethod
    def read(self, path, encoding="utf-8"):
        pass

    @abstractmethod
    def read_text(self, path, encoding="utf-8"):
        pass

    @abstractmethod
    def read_binary(self, path, max_bytes=1048576):
        pass

    @abstractmethod
    def write(self, path, content, overwrite=True):
        pass

    @abstractmethod
    def write_text(self, path, content, encoding="utf-8"):
        pass

    @abstractmethod
    def append(self, path, content):
        pass

    @abstractmethod
    def prepend(self, path, content):
        pass

    @abstractmethod
    def insert(self, path, content, position):
        pass

    @abstractmethod
    def replace_string(self, path, old, new):
        pass

    @abstractmethod
    def clear(self, path):
        pass

    @abstractmethod
    def get_preview(self, path, limit=1000):
        pass


class FileSearch(ABC):
    @abstractmethod
    def find(self, directory, pattern, recursive):
        pass

    @abstractmethod
    def find_by_name(self, directory, name, recursive):
        pass

    @abstractmethod
    def find_by_extension(self, directory, extension, recursive):
        pass

    @abstractmethod
    def find_by_type(self, directory, f_type, recursive):
        pass

    @abstractmethod
    def find_by_size(self, directory, min_size, max_size, recursive):
        pass

    @abstractmethod
    def find_by_date(self, directory, after, before, recursive):
        pass

    @abstractmethod
    def find_by_content(self, directory, query, extensions, recursive):
        pass

    @abstractmethod
    def get_recent(self, directory, days):
        pass

    @abstractmethod
    def get_largest(self, directory, limit):
        pass

    @abstractmethod
    def find_duplicates(self, directory, recursive):
        pass


class FileOrganization(ABC):
    @abstractmethod
    def move_batch(self, files, destination):
        pass

    @abstractmethod
    def copy_batch(self, files, destination):
        pass

    @abstractmethod
    def rename_batch(self, directory, pattern, template):
        pass

    @abstractmethod
    def delete_batch(self, files):
        pass

    @abstractmethod
    def apply_rules(self, directory, rules):
        pass

    @abstractmethod
    def group_by_type(self, directory):
        pass

    @abstractmethod
    def group_by_date(self, directory, granularity):
        pass

    @abstractmethod
    def get_sorted_list(self, directory, by, order):
        pass

    @abstractmethod
    def flatten(self, directory, strategy):
        pass


class FilePermissions(ABC):
    @abstractmethod
    def get_permissions(self, path):
        pass

    @abstractmethod
    def set_permissions(self, path, mode):
        pass

    @abstractmethod
    def add_permission(self, path, target, perm):
        pass

    @abstractmethod
    def remove_permission(self, path, target, perm):
        pass

    @abstractmethod
    def get_owner(self, path):
        pass

    @abstractmethod
    def set_owner(self, path, owner):
        pass

    @abstractmethod
    def get_group(self, path):
        pass

    @abstractmethod
    def set_group(self, path, group):
        pass

    @abstractmethod
    def can_read(self, path):
        pass

    @abstractmethod
    def can_write(self, path):
        pass

    @abstractmethod
    def can_execute(self, path):
        pass


class FileLinks(ABC):
    @abstractmethod
    def create_symlink(self, target, link):
        pass

    @abstractmethod
    def create_hardlink(self, target, link):
        pass

    @abstractmethod
    def read_symlink(self, path):
        pass

    @abstractmethod
    def get_final_target(self, path):
        pass

    @abstractmethod
    def remove_link(self, path):
        pass

    @abstractmethod
    def resolve_full_path(self, path):
        pass


class FileArchive(ABC):
    @abstractmethod
    def create(self, files, destination, fmt):
        pass

    @abstractmethod
    def extract(self, archive, destination):
        pass

    @abstractmethod
    def list_contents(self, archive):
        pass

    @abstractmethod
    def add_files(self, archive, files):
        pass

    @abstractmethod
    def remove_files(self, archive, names):
        pass

    @abstractmethod
    def test(self, archive):
        pass

    @abstractmethod
    def get_info(self, archive):
        pass


class FileComparison(ABC):
    @abstractmethod
    def compare_files(self, f1, f2):
        pass

    @abstractmethod
    def compare_contents(self, f1, f2):
        pass

    @abstractmethod
    def get_hash(self, path, alg):
        pass

    @abstractmethod
    def verify_hash(self, path, expected, alg):
        pass

    @abstractmethod
    def get_diff(self, f1, f2):
        pass

    @abstractmethod
    def is_identical(self, f1, f2):
        pass


class FileDisk(ABC):
    @abstractmethod
    def get_file_usage(self, path):
        pass

    @abstractmethod
    def get_directory_usage(self, path):
        pass

    @abstractmethod
    def get_system_usage(self, path):
        pass

    @abstractmethod
    def find_largest_files(self, path, limit, recursive):
        pass

    @abstractmethod
    def find_largest_directories(self, path, limit):
        pass

    @abstractmethod
    def get_statistics(self, path):
        pass


class FileTemporary(ABC):
    @abstractmethod
    def create_file(self, prefix, suffix, content):
        pass

    @abstractmethod
    def create_directory(self, prefix):
        pass

    @abstractmethod
    def get_system_temp_path(self):
        pass

    @abstractmethod
    def delete_file(self, path):
        pass

    @abstractmethod
    def delete_directory(self, path):
        pass

    @abstractmethod
    def cleanup_all(self, prefix):
        pass


class FileSystem(ABC):
    @abstractmethod
    def open(self, path):
        pass

    @abstractmethod
    def open_with(self, path, application):
        pass

    @abstractmethod
    def reveal(self, path):
        pass

    @abstractmethod
    def get_default_app(self, path):
        pass

    @abstractmethod
    def set_default_app(self, path, application):
        pass

    @abstractmethod
    def lock(self, path):
        pass

    @abstractmethod
    def unlock(self, path):
        pass

    @abstractmethod
    def is_locked(self, path):
        pass


class SystemFile(
    FileInformation,
    FileLifecycle,
    FileContent,
    FileSearch,
    FileOrganization,
    FilePermissions,
    FileLinks,
    FileArchive,
    FileComparison,
    FileDisk,
    FileTemporary,
    FileSystem,
    ABC,
):
    @abstractmethod
    def get_file_info(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_metadata(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_size(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_type(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_extension(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_mime_type(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_path(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_name(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_created_time(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_modified_time(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_accessed_time(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_symlink(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_file_accessible(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def restore_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def trash_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def empty_trash(self, *args, **kwargs):
        pass

    @abstractmethod
    def rename_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def copy_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def move_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def duplicate_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def replace_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def read_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def write_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def append_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def prepend_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def read_lines(self, *args, **kwargs):
        pass

    @abstractmethod
    def write_lines(self, *args, **kwargs):
        pass

    @abstractmethod
    def insert_lines(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_lines(self, *args, **kwargs):
        pass

    @abstractmethod
    def replace_text(self, *args, **kwargs):
        pass

    @abstractmethod
    def find_in_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def delete_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def walk_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def find_files(self, *args, **kwargs):
        pass

    @abstractmethod
    def find_directories(self, *args, **kwargs):
        pass

    @abstractmethod
    def find_by_pattern(self, *args, **kwargs):
        pass

    @abstractmethod
    def find_by_extension(self, *args, **kwargs):
        pass

    @abstractmethod
    def find_by_size(self, *args, **kwargs):
        pass

    @abstractmethod
    def find_by_date(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_symbolic_link(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_hard_link(self, *args, **kwargs):
        pass

    @abstractmethod
    def read_symbolic_link(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_link_target(self, *args, **kwargs):
        pass

    @abstractmethod
    def remove_link(self, *args, **kwargs):
        pass

    @abstractmethod
    def resolve_path(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_archive(self, *args, **kwargs):
        pass

    @abstractmethod
    def extract_archive(self, *args, **kwargs):
        pass

    @abstractmethod
    def list_archive_contents(self, *args, **kwargs):
        pass

    @abstractmethod
    def add_to_archive(self, *args, **kwargs):
        pass

    @abstractmethod
    def remove_from_archive(self, *args, **kwargs):
        pass

    @abstractmethod
    def test_archive(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_archive_info(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_permissions(self, *args, **kwargs):
        pass

    @abstractmethod
    def set_file_permissions(self, *args, **kwargs):
        pass

    @abstractmethod
    def add_file_permission(self, *args, **kwargs):
        pass

    @abstractmethod
    def remove_file_permission(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_owner(self, *args, **kwargs):
        pass

    @abstractmethod
    def set_file_owner(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_group(self, *args, **kwargs):
        pass

    @abstractmethod
    def set_file_group(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_file_readable(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_file_writable(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_file_executable(self, *args, **kwargs):
        pass

    @abstractmethod
    def compare_files(self, *args, **kwargs):
        pass

    @abstractmethod
    def compare_directories(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_file_hash(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_disk_usage(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_free_space(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_directory_size(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_temp_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_temp_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_temp_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def cleanup_temp_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def cleanup_temp_directory(self, *args, **kwargs):
        pass

    @abstractmethod
    def open_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def reveal_in_file_manager(self, *args, **kwargs):
        pass

    @abstractmethod
    def open_with_application(self, *args, **kwargs):
        pass

    @abstractmethod
    def set_file_hidden(self, *args, **kwargs):
        pass

    @abstractmethod
    def is_file_hidden(self, *args, **kwargs):
        pass

    @abstractmethod
    def watch_file(self, *args, **kwargs):
        pass

    @abstractmethod
    def stop_watching(self, *args, **kwargs):
        pass
