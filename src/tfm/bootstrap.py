def bootstrap(seed: int | None = None) -> int:
    """
    Inicializa entorno del TFM:
    - carga .env, aplica TZ, fija semillas, crea rutas.
    Devuelve la seed efectiva.
    """
    import settings  # al importar, settings ejecuta toda la inicialización
    return seed if seed is not None else settings.SEED
