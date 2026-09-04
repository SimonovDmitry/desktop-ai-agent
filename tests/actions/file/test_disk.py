from deskagent.actions.file.disk import GetFileDiskUsage,GetDirectoryDiskUsage,GetDiskUsage,FindLargestFiles,FindLargestDirectories,GetStorageStatistics

def test_file_disk_usage(text_file):
    r=GetFileDiskUsage().execute(None,{'path':str(text_file)}); assert r.success; v=r.data.get('size',r.data.get('disk_usage')); assert isinstance(v,int) and v>=text_file.stat().st_size

def test_directory_disk_usage(sample_tree):
    r=GetDirectoryDiskUsage().execute(None,{'path':str(sample_tree)}); assert r.success; v=r.data.get('size',r.data.get('disk_usage')); assert isinstance(v,int)

def test_disk_usage(sample_tree):
    r=GetDiskUsage().execute(None,{'path':str(sample_tree)}); assert r.success; assert {'total','used','free'}<=set(r.data)

def test_largest_files(sample_tree):
    r=FindLargestFiles().execute(None,{'directory':str(sample_tree),'limit':2}); assert r.success; assert len(r.data.get('files',r.data.get('results',[])))<=2

def test_largest_dirs(sample_tree):
    r=FindLargestDirectories().execute(None,{'directory':str(sample_tree),'limit':2}); assert r.success; assert len(r.data.get('directories',r.data.get('results',[])))<=2

def test_storage_statistics(sample_tree):
    r=GetStorageStatistics().execute(None,{'directory':str(sample_tree),'limit':3}); assert r.success; assert {'total','used','free','usage_percent','largest_files','largest_directories'}<=set(r.data)
