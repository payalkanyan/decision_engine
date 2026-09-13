from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Decision Engine API",
        description="Build vs Partner vs Acquire intelligence, backed by Crustdata",
        version="0.1.0",
    )

    from api.routes import router

    app.include_router(router)
    return app


app = create_app()
