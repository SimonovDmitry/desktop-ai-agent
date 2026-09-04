import os
import stat
import pathlib
import mimetypes
import datetime
import shutil
import base64
import fnmatch
import hashlib
import pwd
import grp
import zipfile
import tarfile
import difflib
import subprocess
import tempfile

from deskagent.platform.base.file import (
    FileInformation, FileLifecycle, FileContent, FileSearch,
    FileOrganization, FilePermissions, FileLinks, FileArchive,
    FileComparison, FileDisk, FileTemporary, FileSystem, FileSystem
)



class MacOSFileInformation(FileInformation):
    def _resolve_path(self, path):
        return os.path.abspath(os.path.expanduser(path))

    def get_info(self, path):
        full_path = self._resolve_path(path)
        s = os.stat(full_path)
        return {
            "path": full_path,
            "name": os.path.basename(full_path),
            "extension": self.get_extension(full_path),
            "type": self.get_type(full_path),
            "size": s.st_size,
            "mime_type": self.get_mime_type(full_path),
            "created_at": self.get_created_at(full_path),
            "modified_at": self.get_modified_at(full_path),
            "accessed_at": self.get_accessed_at(full_path)
        }

    def get_metadata(self, path):
        full_path = self._resolve_path(path)
        s = os.stat(full_path)
        return {
            "size": s.st_size,
            "created_at": self.get_created_at(full_path),
            "modified_at": self.get_modified_at(full_path),
            "permissions": oct(s.st_mode & 0o777),
            "owner_id": s.st_uid,
            "group_id": s.st_gid,
            "is_hidden": os.path.basename(full_path).startswith('.'),
            "is_symlink": os.path.islink(full_path)
        }

    def get_size(self, path):
        return os.path.getsize(self._resolve_path(path))

    def get_type(self, path):
        full_path = self._resolve_path(path)
        if os.path.islink(full_path):
            return "symlink"
        elif os.path.isdir(full_path):
            return "directory"
        elif os.path.isfile(full_path):
            return "file"
        return "unknown"

    def get_extension(self, path):
        return pathlib.Path(path).suffix

    def get_mime_type(self, path):
        mime, _ = mimetypes.guess_type(path)
        return mime or "application/octet-stream"

    def get_absolute_path(self, path):
        return self._resolve_path(path)

    def get_name(self, path):
        return os.path.basename(self._resolve_path(path))

    def get_directory(self, path):
        return os.path.dirname(self._resolve_path(path))

    def get_created_at(self, path):
        s = os.stat(self._resolve_path(path))
        return datetime.datetime.fromtimestamp(s.st_birthtime).isoformat()

    def get_modified_at(self, path):
        s = os.stat(self._resolve_path(path))
        return datetime.datetime.fromtimestamp(s.st_mtime).isoformat()

    def get_accessed_at(self, path):
        s = os.stat(self._resolve_path(path))
        return datetime.datetime.fromtimestamp(s.st_atime).isoformat()

    def is_file(self, path):
        return os.path.isfile(self._resolve_path(path))

    def is_directory(self, path):
        return os.path.isdir(self._resolve_path(path))

    def is_symlink(self, path):
        return os.path.islink(self._resolve_path(path))

    def get_access_permissions(self, path):
        full_path = self._resolve_path(path)
        return {
            "readable": os.access(full_path, os.R_OK),
            "writable": os.access(full_path, os.W_OK),
            "executable": os.access(full_path, os.X_OK)
        }


class MacOSFileLifecycle(FileLifecycle):
    def _resolve_path(self, path):
        return os.path.abspath(os.path.expanduser(path))

    def create(self, path, content=""):
        full_path = self._resolve_path(path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    def delete(self, path):
        full_path = self._resolve_path(path)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return True

    def move_to_trash(self, path):
        full_path = self._resolve_path(path)
        cmd = f"osascript -e 'tell application \"Finder\" to delete POSIX file \"{full_path}\"'"
        os.system(cmd)
        return True

    def restore(self, path):
        name = os.path.basename(path)
        cmd = f"osascript -e 'tell application \"Finder\" to move (every item of trash whose name is \"{name}\") to desktop'"
        os.system(cmd)
        return True

    def empty_trash(self):
        cmd = "osascript -e 'tell application \"Finder\" to empty trash'"
        os.system(cmd)
        return True

    def rename(self, path, new_name):
        full_path = self._resolve_path(path)
        directory = os.path.dirname(full_path)
        new_path = os.path.join(directory, new_name)
        os.rename(full_path, new_path)
        return new_path

    def copy(self, source, destination):
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return True

    def move(self, source, destination):
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)
        shutil.move(src, dst)
        return True

    def duplicate(self, path):
        full_path = self._resolve_path(path)
        p = pathlib.Path(full_path)
        new_path = f"{p.parent}/{p.stem} copy{p.suffix}"
        shutil.copy2(full_path, new_path)
        return new_path

    def replace(self, target, source):
        target_path = self._resolve_path(target)
        source_path = self._resolve_path(source)
        os.replace(source_path, target_path)
        return True


class MacOSFileContent(FileContent):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def read(self, path, encoding="utf-8"):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")
        with open(p, 'r', encoding=encoding) as f:
            content = f.read()
        return content, len(content)

    def read_text(self, path, encoding="utf-8"):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")
        with open(p, 'r', encoding=encoding) as f:
            return f.read()

    def read_binary(self, path, max_bytes=1048576):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")

        size = os.path.getsize(p)

        with open(p, 'rb') as f:
            data = f.read(max_bytes)
        return base64.b64encode(data).decode('utf-8'), size

    def write(self, path, content, overwrite=True):
        p = self._resolve_path(path)
        if not overwrite and os.path.exists(p):
            raise FileExistsError(f"File already exists: {p}")

        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            written = f.write(content)
        return written

    def write_text(self, path, content, encoding="utf-8"):
        p = self._resolve_path(path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding=encoding) as f:
            f.write(content)
        return True

    def append(self, path, content):
        p = self._resolve_path(path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'a', encoding='utf-8') as f:
            f.write(content)
        return True

    def prepend(self, path, content):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            return self.write(p, content)

        with open(p, 'r', encoding='utf-8') as f:
            current_data = f.read()
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content + current_data)
        return True

    def insert(self, path, content, position):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")
        with open(p, 'r', encoding='utf-8') as f:
            data = f.read()
        new_data = data[:position] + content + data[position:]
        with open(p, 'w', encoding='utf-8') as f:
            f.write(new_data)
        return True

    def replace_string(self, path, old, new):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")
        with open(p, 'r', encoding='utf-8') as f:
            data = f.read()
        count = data.count(old)
        new_data = data.replace(old, new)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(new_data)
        return count

    def clear(self, path):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            return False
        with open(p, 'w') as f:
            pass
        return True

    def get_preview(self, path, limit=1000):
        p = self._resolve_path(path)
        if not os.path.exists(p):
            return ""
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(limit)
        except:
            return "[Error reading preview]"


class MacOSFileSearch(FileSearch):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def _get_file_info(self, path):
        return {
            "path": path,
            "name": os.path.basename(path),
            "size": os.path.getsize(path)
        }

    def find(self, directory, pattern="*", recursive=True):
        root_dir = self._resolve_path(directory)
        results = []

        if recursive:
            for root, _, files in os.walk(root_dir):
                for name in files:
                    if fnmatch.fnmatch(name, pattern):
                        results.append(self._get_file_info(os.path.join(root, name)))
        else:
            for name in os.listdir(root_dir):
                full_path = os.path.join(root_dir, name)
                if os.path.isfile(full_path) and fnmatch.fnmatch(name, pattern):
                    results.append(self._get_file_info(full_path))
        return results

    def find_by_name(self, directory, name, recursive=True):
        return self.find(directory, pattern=name, recursive=recursive)

    def find_by_extension(self, directory, extension, recursive=True):
        if not extension.startswith('.'):
            extension = '.' + extension
        return self.find(directory, pattern=f"*{extension}", recursive=recursive)

    def find_by_type(self, directory, f_type, recursive=True):
        type_map = {
            "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"],
            "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
            "video": [".mp4", ".mov", ".avi", ".mkv", ".wmv"],
            "audio": [".mp3", ".wav", ".flac", ".m4a", ".aac"],
            "archive": [".zip", ".tar", ".gz", ".rar", ".7z"],
            "code": [".py", ".js", ".html", ".css", ".cpp", ".c", ".java", ".swift"]
        }
        extensions = type_map.get(f_type.lower(), [])
        root_dir = self._resolve_path(directory)
        results = []

        for root, _, files in os.walk(root_dir) if recursive else [(root_dir, None, os.listdir(root_dir))]:
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path) and pathlib.Path(file).suffix.lower() in extensions:
                    results.append(self._get_file_info(full_path))
        return results

    def find_by_size(self, directory, min_size=None, max_size=None, recursive=True):
        root_dir = self._resolve_path(directory)
        results = []
        for root, _, files in os.walk(root_dir) if recursive else [(root_dir, None, os.listdir(root_dir))]:
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path):
                    size = os.path.getsize(full_path)
                    if (min_size is None or size >= min_size) and (max_size is None or size <= max_size):
                        results.append(self._get_file_info(full_path))
        return results

    def find_by_date(self, directory, after=None, before=None, recursive=True):
        root_dir = self._resolve_path(directory)
        results = []
        dt_after = datetime.datetime.fromisoformat(after).timestamp() if after else None
        dt_before = datetime.datetime.fromisoformat(before).timestamp() if before else None

        for root, _, files in os.walk(root_dir) if recursive else [(root_dir, None, os.listdir(root_dir))]:
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path):
                    mtime = os.path.getmtime(full_path)
                    if (dt_after is None or mtime >= dt_after) and (dt_before is None or mtime <= dt_before):
                        results.append(self._get_file_info(full_path))
        return results

    def find_by_content(self, directory, query, extensions=None, recursive=True):
        root_dir = self._resolve_path(directory)
        results = []
        for root, _, files in os.walk(root_dir) if recursive else [(root_dir, None, os.listdir(root_dir))]:
            for file in files:
                if extensions and not any(file.endswith(ext) for ext in extensions):
                    continue
                full_path = os.path.join(root, file)
                try:
                    if os.path.isfile(full_path):
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            if query in f.read():
                                results.append(self._get_file_info(full_path))
                except:
                    continue
        return results

    def get_recent(self, directory, days=7):
        threshold = (datetime.datetime.now() - datetime.timedelta(days=days)).timestamp()
        root_dir = self._resolve_path(directory)
        results = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path) and os.path.getmtime(full_path) >= threshold:
                    results.append(self._get_file_info(full_path))
        return results

    def get_largest(self, directory, limit=20):
        root_dir = self._resolve_path(directory)
        all_files = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path):
                    all_files.append(self._get_file_info(full_path))
        all_files.sort(key=lambda x: x['size'], reverse=True)
        return all_files[:limit]

    def find_duplicates(self, directory, recursive=True):
        root_dir = self._resolve_path(directory)
        hashes = {}
        for root, _, files in os.walk(root_dir) if recursive else [(root_dir, None, os.listdir(root_dir))]:
            for file in files:
                full_path = os.path.join(root, file)
                if os.path.isfile(full_path):
                    try:
                        h = hashlib.md5(
                            open(full_path, 'rb').read(1024 * 1024)).hexdigest()
                        hashes.setdefault(h, []).append(full_path)
                    except:
                        continue

        return [{"hash": h, "files": paths} for h, paths in hashes.items() if len(paths) > 1]


class MacOSFileOrganization(FileOrganization):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def move_batch(self, files, destination):
        dest_dir = self._resolve_path(destination)
        os.makedirs(dest_dir, exist_ok=True)
        results = []
        for f in files:
            src = self._resolve_path(f)
            if os.path.exists(src):
                new_path = shutil.move(src, dest_dir)
                results.append({"source": src, "result": new_path})
        return results

    def copy_batch(self, files, destination):
        dest_dir = self._resolve_path(destination)
        os.makedirs(dest_dir, exist_ok=True)
        results = []
        for f in files:
            src = self._resolve_path(f)
            if os.path.exists(src):

                new_path = shutil.copy2(src, dest_dir)
                results.append({"source": src, "result": new_path})
        return results

    def rename_batch(self, directory, pattern, template):
        dir_path = self._resolve_path(directory)
        renamed = []
        index = 1
        for filename in sorted(os.listdir(dir_path)):
            if fnmatch.fnmatch(filename, pattern):
                ext = pathlib.Path(filename).suffix
                new_name = template.replace("{index}", str(index))

                if not pathlib.Path(new_name).suffix:
                    new_name += ext

                os.rename(os.path.join(dir_path, filename), os.path.join(dir_path, new_name))
                renamed.append(new_name)
                index += 1
        return renamed

    def delete_batch(self, files):
        for f in files:
            path = self._resolve_path(f)
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        return True

    def apply_rules(self, directory, rules):
        dir_path = self._resolve_path(directory)
        report = []
        for filename in os.listdir(dir_path):
            full_path = os.path.join(dir_path, filename)
            if not os.path.isfile(full_path):
                continue

            ext = pathlib.Path(filename).suffix.lower()
            for rule in rules:
                if ext in [e.lower() for e in rule['extension']]:
                    dest = self._resolve_path(rule['destination'])
                    os.makedirs(dest, exist_ok=True)
                    shutil.move(full_path, dest)
                    report.append({"file": filename, "to": dest})
                    break
        return report

    def group_by_type(self, directory):
        type_rules = [
            {'extension': ['.jpg', '.jpeg', '.png', '.gif', '.webp'], 'destination': 'Images'},
            {'extension': ['.mp4', '.mov', '.avi', '.mkv'], 'destination': 'Video'},
            {'extension': ['.pdf', '.doc', '.docx', '.txt', '.pages'], 'destination': 'Documents'},
            {'extension': ['.zip', '.tar', '.gz', '.rar'], 'destination': 'Archives'},
            {'extension': ['.py', '.js', '.html', '.css', '.cpp'], 'destination': 'Code'}
        ]
        dir_path = self._resolve_path(directory)
        rules = []
        for r in type_rules:
            rules.append({
                'extension': r['extension'],
                'destination': os.path.join(dir_path, r['destination'])
            })

        results = self.apply_rules(dir_path, rules)

        groups = {}
        for item in results:
            folder = os.path.basename(item['to'])
            groups.setdefault(folder, []).append(item['file'])
        return groups

    def group_by_date(self, directory, granularity="month"):
        dir_path = self._resolve_path(directory)
        for filename in os.listdir(dir_path):
            full_path = os.path.join(dir_path, filename)
            if not os.path.isfile(full_path):
                continue

            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
            if granularity == "year":
                sub_path = mtime.strftime("%Y")
            elif granularity == "day":
                sub_path = mtime.strftime("%Y/%m/%d")
            else:
                sub_path = mtime.strftime("%Y/%m")

            dest_dir = os.path.join(dir_path, sub_path)
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(full_path, dest_dir)
        return True

    def get_sorted_list(self, directory, by="name", order="asc"):
        dir_path = self._resolve_path(directory)
        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]

        key_func = None
        if by == "size":
            key_func = lambda x: os.path.getsize(os.path.join(dir_path, x))
        elif by == "modified":
            key_func = lambda x: os.path.getmtime(os.path.join(dir_path, x))
        elif by == "created":
            key_func = lambda x: os.stat(os.path.join(dir_path, x)).st_birthtime
        elif by == "extension":
            key_func = lambda x: pathlib.Path(x).suffix
        else:
            key_func = lambda x: x.lower()

        files.sort(key=key_func, reverse=(order == "desc"))
        return files

    def flatten(self, directory, strategy="rename"):
        root_dir = self._resolve_path(directory)
        count = 0
        for root, dirs, files in os.walk(root_dir, topdown=False):
            if root == root_dir: continue

            for name in files:
                src = os.path.join(root, name)
                dst = os.path.join(root_dir, name)

                if os.path.exists(dst) and strategy == "rename":
                    stem = pathlib.Path(name).stem
                    ext = pathlib.Path(name).suffix
                    i = 1
                    while os.path.exists(os.path.join(root_dir, f"{stem}_{i}{ext}")):
                        i += 1
                    dst = os.path.join(root_dir, f"{stem}_{i}{ext}")

                shutil.move(src, dst)
                count += 1

            try:
                os.rmdir(root)
            except:
                pass
        return count


class MacOSFilePermissions(FilePermissions):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def _get_bit(self, target, perm):
        mapping = {
            ("owner", "read"): stat.S_IRUSR,
            ("owner", "write"): stat.S_IWUSR,
            ("owner", "execute"): stat.S_IXUSR,
            ("group", "read"): stat.S_IRGRP,
            ("group", "write"): stat.S_IWGRP,
            ("group", "execute"): stat.S_IXGRP,
            ("others", "read"): stat.S_IROTH,
            ("others", "write"): stat.S_IWOTH,
            ("others", "execute"): stat.S_IXOTH,
        }
        return mapping.get((target, perm))

    def get_permissions(self, path):
        p = self._resolve_path(path)
        s = os.stat(p)
        mode = s.st_mode

        return {
            "mode": oct(mode & 0o777),
            "owner": {
                "read": bool(mode & stat.S_IRUSR),
                "write": bool(mode & stat.S_IWUSR),
                "execute": bool(mode & stat.S_IXUSR)
            },
            "group": {
                "read": bool(mode & stat.S_IRGRP),
                "write": bool(mode & stat.S_IWGRP),
                "execute": bool(mode & stat.S_IXGRP)
            },
            "others": {
                "read": bool(mode & stat.S_IROTH),
                "write": bool(mode & stat.S_IWOTH),
                "execute": bool(mode & stat.S_IXOTH)
            }
        }

    def set_permissions(self, path, mode):
        p = self._resolve_path(path)
        numeric_mode = int(mode, 8)
        os.chmod(p, numeric_mode)
        return True

    def add_permission(self, path, target, perm):
        p = self._resolve_path(path)
        current_mode = os.stat(p).st_mode
        bit = self._get_bit(target, perm)
        if bit:
            os.chmod(p, current_mode | bit)
            return True
        return False

    def remove_permission(self, path, target, perm):
        p = self._resolve_path(path)
        current_mode = os.stat(p).st_mode
        bit = self._get_bit(target, perm)
        if bit:
            os.chmod(p, current_mode & ~bit)
            return True
        return False

    def get_owner(self, path):
        p = self._resolve_path(path)
        uid = os.stat(p).st_uid
        return pwd.getpwuid(uid).pw_name

    def set_owner(self, path, owner):
        p = self._resolve_path(path)
        uid = pwd.getpwnam(owner).pw_uid
        os.chown(p, uid, -1)
        return True

    def get_group(self, path):
        p = self._resolve_path(path)
        gid = os.stat(p).st_gid
        return grp.getgrgid(gid).gr_name

    def set_group(self, path, group):
        p = self._resolve_path(path)
        gid = grp.getgrnam(group).gr_gid
        os.chown(p, -1, gid)
        return True

    def can_read(self, path):
        return os.access(self._resolve_path(path), os.R_OK)

    def can_write(self, path):
        return os.access(self._resolve_path(path), os.W_OK)

    def can_execute(self, path):
        return os.access(self._resolve_path(path), os.X_OK)


class MacOSFileLinks(FileLinks):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def create_symlink(self, target, link):
        src = self._resolve_path(target)
        dst = self._resolve_path(link)
        os.symlink(src, dst)
        return True

    def create_hardlink(self, target, link):
        src = self._resolve_path(target)
        dst = self._resolve_path(link)
        os.link(src, dst)
        return True

    def read_symlink(self, path):
        p = self._resolve_path(path)
        return os.readlink(p)

    def get_final_target(self, path):
        p = self._resolve_path(path)
        return os.path.realpath(p)

    def remove_link(self, path):
        p = self._resolve_path(path)
        if os.path.islink(p):
            os.unlink(p)
            return True
        return False

    def resolve_full_path(self, path):
        p = pathlib.Path(path).expanduser()
        return str(p.resolve())


class MacOSFileArchive(FileArchive):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def create(self, files, destination, fmt="zip"):
        dest = self._resolve_path(destination)

        if fmt == "zip":
            with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    f_path = self._resolve_path(f)
                    if os.path.isfile(f_path):
                        zf.write(f_path, os.path.basename(f_path))
                    elif os.path.isdir(f_path):
                        for root, _, filenames in os.walk(f_path):
                            for name in filenames:
                                full_p = os.path.join(root, name)
                                zf.write(full_p, os.path.relpath(full_p, os.path.dirname(f_path)))
        else:
            mode = "w:gz" if fmt == "gztar" else "w"
            with tarfile.open(dest, mode) as tf:
                for f in files:
                    tf.add(self._resolve_path(f), arcname=os.path.basename(f))

        return {"size": os.path.getsize(dest)}

    def extract(self, archive, destination):
        arc_path = self._resolve_path(archive)
        dest_path = self._resolve_path(destination)
        os.makedirs(dest_path, exist_ok=True)
        shutil.unpack_archive(arc_path, dest_path)
        return True

    def list_contents(self, archive):
        path = self._resolve_path(archive)
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, 'r') as zf:
                return zf.namelist()
        elif tarfile.is_tarfile(path):
            with tarfile.open(path, 'r') as tf:
                return tf.getnames()
        return []

    def add_files(self, archive, files):
        path = self._resolve_path(archive)
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, 'a') as zf:
                for f in files:
                    f_path = self._resolve_path(f)
                    zf.write(f_path, os.path.basename(f_path))
            return True
        return False

    def remove_files(self, archive, names):
        path = self._resolve_path(archive)
        if not zipfile.is_zipfile(path): return False

        temp_arc = path + ".temp"
        with zipfile.ZipFile(path, 'r') as zin:
            with zipfile.ZipFile(temp_arc, 'w') as zout:
                for item in zin.infolist():
                    if item.filename not in names:
                        zout.writestr(item, zin.read(item.filename))

        os.replace(temp_arc, path)
        return True

    def test(self, archive):
        path = self._resolve_path(archive)
        try:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, 'r') as zf:
                    return zf.testzip() is None
            elif tarfile.is_tarfile(path):
                with tarfile.open(path, 'r') as tf:
                    for member in tf: pass
                return True
        except:
            return False
        return False

    def get_info(self, archive):
        path = self._resolve_path(pathlib.Path(archive))
        size = os.path.getsize(path)
        fmt = "unknown"
        entries = 0

        if zipfile.is_zipfile(path):
            fmt = "zip"
            with zipfile.ZipFile(path, 'r') as zf:
                entries = len(zf.infolist())
        elif tarfile.is_tarfile(path):
            fmt = "tar"
            with tarfile.open(path, 'r') as tf:
                entries = len(tf.getmembers())

        return {
            "format": fmt,
            "size": size,
            "entries": entries
        }


class MacOSFileComparison(FileComparison):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def get_hash(self, path, alg="sha256"):
        p = self._resolve_path(path)
        hash_func = hashlib.new(alg)
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def compare_files(self, f1, f2):
        p1, p2 = self._resolve_path(f1), self._resolve_path(f2)

        size1 = os.path.getsize(p1)
        size2 = os.path.getsize(p2)

        if size1 != size2:
            return {"identical": False, "size_equal": False, "hash_equal": False}

        h1 = self.get_hash(p1)
        h2 = self.get_hash(p2)

        return {
            "identical": h1 == h2,
            "size_equal": True,
            "hash_equal": h1 == h2
        }

    def compare_contents(self, f1, f2):
        identical = self.is_identical(f1, f2)
        diff = [] if identical else self.get_diff(f1, f2)

        return {
            "identical": identical,
            "differences_count": len(diff)
        }

    def verify_hash(self, path, expected, alg="sha256"):

        current_hash = self.get_hash(path, alg)
        return current_hash.lower() == expected.lower()

    def get_diff(self, f1, f2):

        p1, p2 = self._resolve_path(f1), self._resolve_path(f2)

        with open(p1, 'r', encoding='utf-8', errors='ignore') as file1:
            with open(p2, 'r', encoding='utf-8', errors='ignore') as file2:
                diff = difflib.unified_diff(
                    file1.readlines(),
                    file2.readlines(),
                    fromfile=os.path.basename(p1),
                    tofile=os.path.basename(p2)
                )
                return list(diff)

    def is_identical(self, f1, f2):
        p1, p2 = self._resolve_path(f1), self._resolve_path(f2)
        if os.path.getsize(p1) != os.path.getsize(p2):
            return False
        return self.get_hash(p1) == self.get_hash(p2)


class MacOSFileDisk(FileDisk):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def get_file_usage(self, path):
        p = self._resolve_path(path)
        s = os.stat(p)
        return s.st_blocks * 512

    def get_directory_usage(self, path):
        root_dir = self._resolve_path(path)
        total_size = 0
        file_count = 0
        dir_count = 0

        for root, dirs, files in os.walk(root_dir):
            dir_count += len(dirs)
            file_count += len(files)
            for f in files:
                fp = os.path.join(root, f)

                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return {
            "size": total_size,
            "files": file_count,
            "directories": dir_count
        }

    def get_system_usage(self, path="/"):
        p = self._resolve_path(path)
        usage = shutil.disk_usage(p)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": round((usage.used / usage.total) * 100, 2)
        }

    def find_largest_files(self, path="/", limit=10, recursive=True):
        root_dir = self._resolve_path(path)
        all_files = []

        if recursive:
            for root, _, files in os.walk(root_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        if not os.path.islink(fp):
                            all_files.append({"path": fp, "size": os.path.getsize(fp)})
                    except:
                        continue
        else:
            for f in os.listdir(root_dir):
                fp = os.path.join(root_dir, f)
                if os.path.isfile(fp) and not os.path.islink(fp):
                    all_files.append({"path": fp, "size": os.path.getsize(fp)})

        all_files.sort(key=lambda x: x['size'], reverse=True)
        return all_files[:limit]

    def find_largest_directories(self, path, limit=5):
        root_dir = self._resolve_path(path)
        dir_sizes = []

        try:
            for item in os.listdir(root_dir):
                item_path = os.path.join(root_dir, item)
                if os.path.isdir(item_path) and not os.path.islink(item_path):
                    usage = self.get_directory_usage(item_path)
                    dir_sizes.append({"path": item_path, "size": usage['size']})
        except:
            pass

        dir_sizes.sort(key=lambda x: x['size'], reverse=True)
        return dir_sizes[:limit]

    def get_statistics(self, path="/"):
        p = self._resolve_path(path)
        sys_usage = self.get_system_usage(p)

        return {
            "disk": sys_usage,
            "largest_files": self.find_largest_files(p, limit=5),
            "largest_directories": self.find_largest_directories(p, limit=5)
        }


class MacOSFileTemporary(FileTemporary):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def create_file(self, prefix="agent_", suffix=".tmp", content=None):
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)

        try:
            if content:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                os.close(fd)
        except Exception as e:
            os.close(fd)
            raise e

        return path

    def create_directory(self, prefix="agent_dir_"):
        return tempfile.mkdtemp(prefix=prefix)

    def get_system_temp_path(self):
        return tempfile.gettempdir()

    def delete_file(self, path):
        p = self._resolve_path(path)
        if os.path.isfile(p):
            os.remove(p)
            return True
        return False

    def delete_directory(self, path):
        p = self._resolve_path(path)
        if os.path.isdir(p):
            shutil.rmtree(p)
            return True
        return False

    def cleanup_all(self, prefix="agent_"):
        temp_dir = self.get_system_temp_path()
        count = 0

        for item in os.listdir(temp_dir):
            if item.startswith(prefix):
                full_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                    count += 1
                except:
                    continue
        return count


class MacOSFileSystem(FileSystem):
    def _resolve_path(self, path):
        return str(pathlib.Path(path).expanduser().resolve())

    def open(self, path):
        p = self._resolve_path(path)
        subprocess.run(['open', p], check=True)
        return True

    def open_with(self, path, application):
        p = self._resolve_path(path)
        subprocess.run(['open', '-a', application, p], check=True)
        return True

    def reveal(self, path):
        p = self._resolve_path(path)
        subprocess.run(['open', '-R', p], check=True)
        return True

    def get_default_app(self, path):
        p = self._resolve_path(path)
        script = f'''
        set theFile to POSIX file "{p}"
        tell application "Finder"
            set app_path to (default application of item theFile) as text
            return name of file app_path
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else "Unknown"

    def set_default_app(self, path, application):
        p = self._resolve_path(path)
        script = f'''
        tell application "Finder"
            set theFile to POSIX file "{p}"
            set default application of item theFile to application "{application}"
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script])
        return result.returncode == 0

    def lock(self, path):
        p = self._resolve_path(path)
        subprocess.run(['chflags', 'uchg', p], check=True)
        return True

    def unlock(self, path):
        p = self._resolve_path(path)
        subprocess.run(['chflags', 'nouchg', p], check=True)
        return True

    def is_locked(self, path):
        p = self._resolve_path(path)
        s = os.stat(p)
        return bool(s.st_flags & stat.UF_IMMUTABLE)
