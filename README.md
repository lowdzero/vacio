# TR Portfolio Bot — V1

Bot de simulación para una cartera de Trade Republic.

> **Modo simulación únicamente.** Esta versión no se conecta a Trade Republic, no usa credenciales y no ejecuta órdenes reales.

## Objetivo

Construir una base segura para analizar una cartera con prioridad en preservar capital, mantener alta liquidez, limitar pérdidas y registrar operaciones para futura información fiscal.

## Configuración inicial

- Capital simulado: **2,50 €**
- Liquidez objetivo: **90–100 %**
- Perfil: **muy conservador**
- Apalancamiento: **0 %**
- Derivados: **no**
- Operaciones reales: **no**

## V1

Incluye motor de simulación, cartera, registro de operaciones y métricas básicas de rentabilidad y riesgo.

## Ejecución

Requiere Python 3.11+.

```bash
python -m src.main
```

## Seguridad

Nunca introduzcas contraseñas, códigos 2FA, claves de recuperación ni credenciales de Trade Republic. La integración real, si algún día se implementa, deberá revisarse por compatibilidad, seguridad y condiciones del servicio.
