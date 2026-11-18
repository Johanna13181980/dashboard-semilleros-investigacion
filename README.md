# Dashboard de seguimiento de semilleros

## Publicación
1. Suba `app.py`, `requirements.txt` y `.gitignore` a GitHub. **No suba el Excel**.
2. En https://share.streamlit.io/ seleccione Create app y conecte el repositorio.
3. Indique `app.py` como archivo principal y despliegue.
4. Abra la aplicación y cargue el archivo Excel desde el selector.

## Ejecución local
`python -m pip install -r requirements.txt`
`python -m streamlit run app.py`

## Privacidad
El Excel contiene datos personales. El archivo se transmite al servidor que ejecuta la app y puede procesarse en memoria. No hay almacenamiento persistente implementado por este código, pero una app pública no ofrece control de acceso suficiente para datos sensibles. Para un despliegue público, use un Excel anonimizado y sin identificadores personales, o un entorno privado con autenticación.
