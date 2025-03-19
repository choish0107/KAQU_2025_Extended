from setuptools import find_packages, setup

package_name = 'stt_whisper'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        # 'faster-whisper',
        ],
    zip_safe=True,
    maintainer='hajun',
    maintainer_email='choish0107@daum.net',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'my_stt_whisper = stt_whisper.stt_node:main'
        ],
    },
)