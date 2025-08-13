# database.py
"""
DocuReview Pro - Database Setup and SQLAlchemy Models
Enterprise Document Version Management & Analysis System
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import Config

# Database setup
DATABASE_URL = f"sqlite:///{Config.DB_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=Config.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Document(Base):
    """Document model for version management"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author = Column(String(255))
    source = Column(String(500))
    domain = Column(String(255))
    tags = Column(Text)  # JSON or comma-separated
    notes = Column(Text)
    checksum = Column(String(64))  # SHA256
    bytes = Column(Integer)
    status = Column(String(50), default='uploaded')  # uploaded|analyzing|indexed|error
    
    # Relationships
    files = relationship("File", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    vector_indexes = relationship("VectorIndex", back_populates="document", cascade="all, delete-orphan")
    
    # Unique constraint on slug + version
    __table_args__ = (Index('ux_doc_slug_version', 'slug', 'version', unique=True),)

class File(Base):
    """File metadata for uploaded documents"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    filename = Column(String(255))
    path = Column(String(1000), nullable=False)
    mime = Column(String(100))
    size = Column(Integer)
    
    # Relationships
    document = relationship("Document", back_populates="files")

class Chunk(Base):
    """Text chunks with AI analysis"""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_ix = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    token_start = Column(Integer)
    token_end = Column(Integer)
    heading = Column(String(500))
    subheading = Column(String(500))
    intent_label = Column(String(100))  # overview/design/risk/requirements/etc
    summary = Column(Text)
    key_values = Column(Text)  # JSON
    triples = Column(Text)  # JSON array of (subject, predicate, object)
    similarity_score = Column(Float)  # For comparisons
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

class VectorIndex(Base):
    """FAISS vector index metadata"""
    __tablename__ = "vector_indexes"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    index_type = Column(String(100), default="faiss:FlatIP")
    dim = Column(Integer, nullable=False)
    path = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="vector_indexes")

class Comparison(Base):
    """Document version comparisons cache"""
    __tablename__ = "comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_slug = Column(String(255), nullable=False)
    version_a = Column(Integer, nullable=False)
    version_b = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Comparison results (JSON stored as text)
    text_diff_json = Column(Text)  # Text-level differences
    section_map_json = Column(Text)  # Section alignment mapping
    metrics_json = Column(Text)  # Computed similarity metrics
    llm_summary = Column(Text)  # AI-generated change summary
    
    # Performance metrics
    processing_time_ms = Column(Float)
    similarity_score = Column(Float)  # Overall similarity (0-1)
    change_score = Column(Float)  # Overall change intensity (0-1)

class DiffConfiguration(Base):
    """User-configurable diff settings"""
    __tablename__ = "diff_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    granularity = Column(String(50), default='word')  # character|word|sentence|paragraph
    algorithm = Column(String(50), default='hybrid')  # syntactic|semantic|hybrid
    color_scheme = Column(String(100), default='default')
    similarity_threshold = Column(Float, default=0.8)
    show_only_changes = Column(String(10), default='false')  # boolean as string
    created_at = Column(DateTime, default=datetime.utcnow)
    is_default = Column(String(10), default='false')

class AuditLog(Base):
    """Audit trail for all operations"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    operation = Column(String(100), nullable=False)  # upload|analyze|compare|delete
    entity_type = Column(String(50))  # document|chunk|comparison
    entity_id = Column(Integer)
    details = Column(Text)  # JSON with operation details
    user_info = Column(String(255))  # IP, user agent, etc.
    execution_time_ms = Column(Float)

# Database functions
def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables and default data"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Insert default diff configuration
        db = SessionLocal()
        try:
            # Check if default config exists
            default_config = db.query(DiffConfiguration).filter(
                DiffConfiguration.is_default == 'true'
            ).first()
            
            if not default_config:
                default_config = DiffConfiguration(
                    name="Default Configuration",
                    granularity="word",
                    algorithm="hybrid",
                    color_scheme="default",
                    similarity_threshold=0.8,
                    show_only_changes="false",
                    is_default="true"
                )
                db.add(default_config)
                db.commit()
                print("✅ Default diff configuration created")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not create default configuration: {e}")
            db.rollback()
        finally:
            db.close()
            
        print(f"✅ Database initialized at {Config.get_database_path()}")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

def execute_raw_sql(query: str, params: tuple = None):
    """
    Execute raw SQL query for admin operations
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Query parameters
    
    Returns:
        dict: Query results with metadata
    
    Example:
        result = execute_raw_sql("SELECT * FROM documents LIMIT 5")
        result = execute_raw_sql("SELECT * FROM documents WHERE id = ?", (1,))
    """
    try:
        # Use direct sqlite3 connection for raw queries
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column name access
        cursor = conn.cursor()
        
        start_time = datetime.utcnow()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Handle different query types
        if query.strip().upper().startswith(('SELECT', 'WITH', 'PRAGMA')):
            # Query with results
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            result = {
                "success": True,
                "query_type": "SELECT",
                "rows": [dict(row) for row in rows],
                "columns": columns,
                "row_count": len(rows),
                "execution_time_ms": round(execution_time, 2)
            }
        else:
            # DML/DDL operation
            conn.commit()
            result = {
                "success": True,
                "query_type": "DML/DDL",
                "rows_affected": cursor.rowcount,
                "execution_time_ms": round(execution_time, 2)
            }
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query[:200] + "..." if len(query) > 200 else query
        }

if __name__ == "__main__":
    # Test database initialization
    print("🧪 Testing database initialization...")
    init_database()
    
    # Test raw SQL execution
    print("\n🧪 Testing raw SQL execution...")
    result = execute_raw_sql("SELECT name FROM sqlite_master WHERE type='table'")
    print(f"Tables found: {result}")
    
    print("\n✅ Database module test completed!")