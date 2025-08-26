{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
	name = "MapPy";

	buildInputs = with pkgs; [
		python3Packages.pip
		python3Packages.wheel

		python3Packages.pandas
		python3Packages.numpy
		python3Packages.openpyxl

		python3Packages.plotly
		python3Packages.matplotlib
		python3Packages.seaborn

		python3Packages.reportlab
		python3Packages.pillow

		python3Packages.streamlit
	];

	shellHook = ''
		if [ ! -d "venv" ]; then
		    python -m venv venv
		fi
		source venv/bin/activate

		pip install --quiet folium streamlit-folium geopandas

		pip install --quiet --upgrade streamlit

		fish
	'';
}
