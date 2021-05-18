from setuptools import setup


setup(
    name='FieldLinguisticsIde',
    version='0.0.1',
    description='IDE for managing language field data',
    url='https://github.com/OneAdder/field_linguistics_ide',
    author='Michael Voronov',
    author_email='mikivo@list.ru',
    license='GPLv3',
    packages=['field_linguistics_ide',
              'field_linguistics_ide.loaders',
              'field_linguistics_ide.user_interface',
              'field_linguistics_ide.user_interface.templates',
              'field_linguistics_ide.user_interface.widgets',
              'field_linguistics_ide.user_interface.widgets.document_area',
              ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'field-lingustics-ide=field_linguistics_ide.user_interface.main:main',
        ],
    },
    include_package_data=True,
)

