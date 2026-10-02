# Investment Decision Lab

Aplicación web de análisis de activos y cartera orientada a toma de decisiones informada. Es **analysis-only**: no conecta con brokers ni ejecuta órdenes.

## Incluye

- Datos de mercado con marca de tiempo y control de frescura.
- Precio, SMA20/50/200, RSI14, MACD, volatilidad, máximos y mínimos de 52 semanas y volumen medio.
- Análisis por factores: tendencia, momentum y riesgo.
- Estados `ENTRADA CONDICIONADA`, `ESPERAR` y `NO ENTRAR`.
- Zona de entrada orientativa y plan de entradas escalonadas.
- Cálculo de tamaño por capital, reserva de efectivo, riesgo por operación y máximo por activo.
- Condiciones que pueden invalidar la tesis.
- Cartera local con SQLite, pesos y P/L aproximado.
- Alertas de precio almacenadas localmente.
- Noticias mediante el buscador de Yahoo Finance.
- Backtesting sencillo con advertencia explícita sobre el carácter histórico.
- Interfaz responsive en español.

## Regla de datos

La aplicación no debe inventar precios, noticias ni indicadores. Si el proveedor falla, faltan datos o la última observación supera el umbral de frescura configurado, la señal se bloquea y se muestra `ESPERAR`.

## Ejecutar

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000`.

## Arquitectura

- `app.py`: API Flask y rutas web.
- `data_provider.py`: proveedor de datos externo y control de frescura.
- `analysis_engine.py`: indicadores, análisis, sizing, cartera y backtest.
- `storage.py`: persistencia SQLite local.
- `templates/index.html`: interfaz.

## Límites del MVP

Los datos proceden de servicios externos y deben verificarse antes de tomar decisiones. Las métricas técnicas no constituyen una garantía de rentabilidad. La valoración fundamental completa, correlaciones avanzadas, exposición sectorial/geográfica/monetaria y un sistema de alertas push requieren proveedores y módulos adicionales.

No se almacenan credenciales de broker y no existe ejecución de órdenes.
