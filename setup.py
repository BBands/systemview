from setuptools import setup

setup(name='SystemView',
	version='0.1',
	description='Trading system visualisation.',
	url='https://bitbucket.org/BBands/systemview',
	author='John Bollinger',
	author_email='bbands@gmail.com',
	license='MIT',
	packages=['matplotlib', 'numpy'],
	install_requires=[
		'numpy',
		'matplotlib',
	],
	data_files=[('sample_data', ['spx.csv'])],
	zip_safe=False)