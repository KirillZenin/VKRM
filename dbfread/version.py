from collections import namedtuple

VersionInfo = namedtuple('VersionInfo',
                         ['major', 'minor', 'micro', 'patch', 'releaselevel', 'serial'])

def _make_version_info(version):
    if '-' in version:
        version, releaselevel = version.split('-')
    else:
        releaselevel = ''

    if version.count('.') == 3:
        major, minor, micro, patch = map(int, version.split('.'))
    else:
        major, minor, micro = map(int, version.split('.'))
        patch = 0

    return VersionInfo(major, minor, micro, patch, releaselevel, 0)

version = '2.0.7.2'
version_info = _make_version_info(version)
