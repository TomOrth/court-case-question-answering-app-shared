"""
Preprocessing pipeline stages.

The pipeline is divided into three independent stages:
1. Fetch - Get data from Clearinghouse API
2. Process - Heavy computation (chunking, embeddings, summarization)
3. Persist - Save everything to database in one transaction
"""

from .fetch import FetchStage
from .process import ProcessStage
from .persist import PersistStage

__all__ = ['FetchStage', 'ProcessStage', 'PersistStage']
