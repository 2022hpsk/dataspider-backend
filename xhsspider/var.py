from contextvars import ContextVar

crawler_type_var: ContextVar[str] = ContextVar("crawler_type", default="")
source_keyword_var: ContextVar[str] = ContextVar("source_keyword", default="")
