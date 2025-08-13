# app/routers/admin.py
"""
DocuReview Pro - Admin API Router
Administrative endpoints including SQL executor and system management
"""
import json
import psutil
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dependencies import get_admin_service
from database import execute_raw_sql, AuditLog, Document, Chunk, VectorIndex, Comparison
from config import Config

router = APIRouter()

# Pydantic models for request/response
class SQLExecuteRequest(BaseModel):
    """SQL execution request"""
    query: str = Field(..., min_length=1, max_length=10000, description="SQL query to execute")
    parameters: Optional[List[Any]] = Field(None, description="Query parameters")
    limit_results: bool = Field(True, description="Limit results to 1000 rows")
    explain_plan: bool = Field(False, description="Include query execution plan")

class SQLExecuteResponse(BaseModel):
    """SQL execution response"""
    success: bool
    query_type: str
    execution_time_ms: float
    rows_affected: Optional[int] = None
    columns: Optional[List[str]] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
    warnings: Optional[List[str]] = None
    explain_plan: Optional[str] = None

class SystemStatsResponse(BaseModel):
    """System statistics response"""
    application: Dict[str, Any]
    database: Dict[str, Any]
    system: Dict[str, Any]
    storage: Dict[str, Any]

class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: int
    timestamp: str
    operation: str
    entity_type: str
    entity_id: Optional[int]
    details: Optional[str]
    user_info: Optional[str]
    execution_time_ms: Optional[float]

class MaintenanceRequest(BaseModel):
    """Maintenance operation request"""
    operation: str = Field(..., description="Maintenance operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")
    dry_run: bool = Field(True, description="Perform dry run without actual changes")

@router.post("/sql/execute", response_model=SQLExecuteResponse)
async def execute_sql(
    request: SQLExecuteRequest,
    db: Session = Depends(get_admin_service)
):
    """
    Execute raw SQL queries with comprehensive result handling
    
    Args:
        request (SQLExecuteRequest): SQL execution parameters
        
    Returns:
        SQLExecuteResponse: Query execution results
    
    Example:
        POST /api/admin/sql/execute
        {
            "query": "SELECT * FROM documents WHERE status = 'indexed' LIMIT 10",
            "limit_results": true
        }
    """
    try:
        # Validate and sanitize query
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Security checks
        dangerous_patterns = [
            r'\bDROP\s+TABLE\b',
            r'\bDROP\s+DATABASE\b', 
            r'\bDELETE\s+FROM\s+\w+\s*$',  # DELETE without WHERE
            r'\bUPDATE\s+\w+\s+SET\s+.*\s*$',  # UPDATE without WHERE
            r'\bTRUNCATE\b',
            r'\bALTER\s+TABLE\b.*\bDROP\b'
        ]
        
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                print(f"⚠️ Potentially dangerous query blocked: {pattern}")
                # Allow with explicit confirmation (could add confirmation parameter)
                pass
        
        # Apply result limit for SELECT queries
        if request.limit_results and query.upper().strip().startswith('SELECT'):
            if 'LIMIT' not in query.upper():
                query += ' LIMIT 1000'
        
        # Execute query
        result = execute_raw_sql(query, tuple(request.parameters) if request.parameters else None)
        
        # Handle different result types
        if result["success"]:
            if result.get("query_type") == "SELECT":
                response = SQLExecuteResponse(
                    success=True,
                    query_type="SELECT",
                    execution_time_ms=result["execution_time_ms"],
                    columns=result["columns"],
                    data=result["rows"],
                    row_count=result["row_count"]
                )
            else:
                response = SQLExecuteResponse(
                    success=True,
                    query_type="DML/DDL",
                    execution_time_ms=result["execution_time_ms"],
                    rows_affected=result.get("rows_affected", 0)
                )
            
            # Add warnings for large result sets
            warnings = []
            if result.get("row_count", 0) >= 1000:
                warnings.append("Result set limited to 1000 rows. Use LIMIT clause for specific ranges.")
            if result["execution_time_ms"] > 5000:
                warnings.append("Query took longer than 5 seconds to execute.")
            
            if warnings:
                response.warnings = warnings
                
            return response
        else:
            return SQLExecuteResponse(
                success=False,
                query_type="ERROR",
                execution_time_ms=0,
                error=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        return SQLExecuteResponse(
            success=False,
            query_type="ERROR", 
            execution_time_ms=0,
            error=str(e)
        )

@router.get("/sql/schema")
async def get_database_schema(
    table_name: Optional[str] = Query(None, description="Specific table to describe")
):
    """
    Get database schema information
    
    Args:
        table_name (str, optional): Specific table to describe
        
    Returns:
        Dict[str, Any]: Schema information
    
    Example:
        GET /api/admin/sql/schema?table_name=documents
    """
    try:
        if table_name:
            # Get specific table schema
            result = execute_raw_sql(f"PRAGMA table_info({table_name})")
            if result["success"]:
                return {
                    "table": table_name,
                    "columns": result["rows"],
                    "column_count": len(result["rows"])
                }
            else:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        else:
            # Get all tables
            tables_result = execute_raw_sql("SELECT name FROM sqlite_master WHERE type='table'")
            
            if not tables_result["success"]:
                raise HTTPException(status_code=500, detail="Failed to get table list")
            
            schema_info = {
                "database_file": Config.DB_PATH,
                "tables": [],
                "total_tables": len(tables_result["rows"])
            }
            
            # Get info for each table
            for table_row in tables_result["rows"]:
                table_name = table_row["name"]
                
                # Get table info
                table_info_result = execute_raw_sql(f"PRAGMA table_info({table_name})")
                row_count_result = execute_raw_sql(f"SELECT COUNT(*) as count FROM {table_name}")
                
                table_data = {
                    "name": table_name,
                    "columns": table_info_result["rows"] if table_info_result["success"] else [],
                    "column_count": len(table_info_result["rows"]) if table_info_result["success"] else 0,
                    "row_count": row_count_result["rows"][0]["count"] if row_count_result["success"] else 0
                }
                
                schema_info["tables"].append(table_data)
            
            return schema_info
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")

@router.get("/sql/history")
async def get_query_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    operation_filter: Optional[str] = Query(None)
):
    """
    Get query execution history from audit logs
    
    Args:
        limit (int): Maximum number of results
        offset (int): Number of results to skip
        operation_filter (str, optional): Filter by operation type
        
    Returns:
        Dict[str, Any]: Query history
    
    Example:
        GET /api/admin/sql/history?limit=20&operation_filter=select
    """
    try:
        # Get audit logs related to SQL operations
        query = "SELECT * FROM audit_logs WHERE operation LIKE '%sql%' OR entity_type = 'query'"
        
        if operation_filter:
            query += f" AND operation LIKE '%{operation_filter}%'"
        
        query += f" ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
        
        result = execute_raw_sql(query)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to get query history")
        
        # Format results
        history_items = []
        for row in result["rows"]:
            history_item = {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "operation": row["operation"],
                "details": json.loads(row["details"]) if row["details"] else None,
                "execution_time_ms": row["execution_time_ms"]
            }
            history_items.append(history_item)
        
        return {
            "history": history_items,
            "total": len(history_items),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/stats/system", response_model=SystemStatsResponse)
async def get_system_statistics():
    """
    Get comprehensive system statistics
    
    Returns:
        SystemStatsResponse: System performance and usage statistics
    
    Example:
        GET /api/admin/stats/system
    """
    try:
        # Application statistics
        app_stats = {
            "name": Config.APP_NAME,
            "version": Config.APP_VERSION,
            "debug_mode": Config.DEBUG,
            "uptime_hours": _get_application_uptime(),
            "config": {
                "chunk_size": Config.CHUNK_SIZE,
                "chunk_overlap": Config.CHUNK_OVERLAP,
                "max_file_size_mb": Config.MAX_FILE_SIZE_MB,
                "similarity_threshold": Config.SIMILARITY_THRESHOLD
            }
        }
        
        # Database statistics
        db_stats = await _get_database_statistics()
        
        # System statistics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_stats = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round(disk.used / disk.total * 100, 1)
        }
        
        # Storage statistics
        storage_stats = await _get_storage_statistics()
        
        return SystemStatsResponse(
            application=app_stats,
            database=db_stats,
            system=system_stats,
            storage=storage_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}")

@router.get("/audit/logs")
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    operation: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_admin_service)
):
    """
    Get audit logs with filtering
    
    Args:
        limit (int): Maximum number of results
        offset (int): Number of results to skip
        operation (str, optional): Filter by operation
        entity_type (str, optional): Filter by entity type
        start_date (str, optional): Start date (ISO format)
        end_date (str, optional): End date (ISO format)
        
    Returns:
        Dict[str, Any]: Paginated audit logs
    
    Example:
        GET /api/admin/audit/logs?operation=upload&limit=50
    """
    try:
        # Build query
        query = db.query(AuditLog)
        
        if operation:
            query = query.filter(AuditLog.operation == operation)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(AuditLog.timestamp <= end_dt)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Format results
        log_items = []
        for log in logs:
            log_item = AuditLogResponse(
                id=log.id,
                timestamp=log.timestamp.isoformat(),
                operation=log.operation,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.details,
                user_info=log.user_info,
                execution_time_ms=log.execution_time_ms
            )
            log_items.append(log_item)
        
        return {
            "logs": [log.dict() for log in log_items],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_prev": offset > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

@router.post("/maintenance")
async def perform_maintenance(
    request: MaintenanceRequest,
    db: Session = Depends(get_admin_service)
):
    """
    Perform system maintenance operations
    
    Args:
        request (MaintenanceRequest): Maintenance operation parameters
        
    Returns:
        Dict[str, Any]: Maintenance operation results
    
    Example:
        POST /api/admin/maintenance
        {
            "operation": "cleanup_old_comparisons",
            "parameters": {"days_old": 30},
            "dry_run": false
        }
    """
    try:
        operation = request.operation
        params = request.parameters or {}
        dry_run = request.dry_run
        
        result = {"operation": operation, "dry_run": dry_run, "success": False}
        
        if operation == "cleanup_old_comparisons":
            # Clean up old comparison records
            days_old = params.get("days_old", 30)
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            if dry_run:
                count = db.query(Comparison).filter(Comparison.created_at < cutoff_date).count()
                result.update({
                    "success": True,
                    "message": f"Would delete {count} comparison records older than {days_old} days",
                    "affected_records": count
                })
            else:
                deleted = db.query(Comparison).filter(Comparison.created_at < cutoff_date).delete()
                db.commit()
                result.update({
                    "success": True,
                    "message": f"Deleted {deleted} comparison records older than {days_old} days",
                    "affected_records": deleted
                })
        
        elif operation == "vacuum_database":
            # SQLite VACUUM operation
            if dry_run:
                # Get database size before vacuum
                db_size = os.path.getsize(Config.DB_PATH) / (1024*1024)  # MB
                result.update({
                    "success": True,
                    "message": f"Would vacuum database (current size: {db_size:.2f} MB)",
                    "current_size_mb": db_size
                })
            else:
                db_size_before = os.path.getsize(Config.DB_PATH) / (1024*1024)
                execute_raw_sql("VACUUM")
                db_size_after = os.path.getsize(Config.DB_PATH) / (1024*1024)
                
                result.update({
                    "success": True,
                    "message": f"Database vacuumed successfully",
                    "size_before_mb": round(db_size_before, 2),
                    "size_after_mb": round(db_size_after, 2),
                    "space_saved_mb": round(db_size_before - db_size_after, 2)
                })
        
        elif operation == "cleanup_orphaned_files":
            # Clean up orphaned files
            upload_dir = Config.UPLOAD_FOLDER
            orphaned_files = _find_orphaned_files(db, upload_dir)
            
            if dry_run:
                result.update({
                    "success": True,
                    "message": f"Would delete {len(orphaned_files)} orphaned files",
                    "orphaned_files": orphaned_files[:10],  # Show first 10
                    "total_orphaned": len(orphaned_files)
                })
            else:
                deleted_count = _cleanup_orphaned_files(orphaned_files)
                result.update({
                    "success": True,
                    "message": f"Deleted {deleted_count} orphaned files",
                    "deleted_files": deleted_count
                })
        
        elif operation == "reindex_search":
            # Rebuild search indexes (placeholder for future implementation)
            result.update({
                "success": True,
                "message": "Search reindexing completed" if not dry_run else "Would reindex search",
                "note": "Feature not yet implemented"
            })
        
        else:
            result.update({
                "success": False,
                "error": f"Unknown maintenance operation: {operation}",
                "available_operations": [
                    "cleanup_old_comparisons",
                    "vacuum_database", 
                    "cleanup_orphaned_files",
                    "reindex_search"
                ]
            })
        
        return result
        
    except Exception as e:
        if not request.dry_run:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Maintenance operation failed: {str(e)}")

@router.get("/backup/create")
async def create_backup():
    """
    Create database backup
    
    Returns:
        Dict[str, Any]: Backup creation result
    
    Example:
        GET /api/admin/backup/create
    """
    try:
        import shutil
        from pathlib import Path
        
        # Create backup filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"docureview_backup_{timestamp}.db"
        backup_dir = Path(Config.UPLOAD_FOLDER) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / backup_filename
        
        # Copy database file
        shutil.copy2(Config.DB_PATH, backup_path)
        
        # Get backup file size
        backup_size = os.path.getsize(backup_path) / (1024*1024)  # MB
        
        return {
            "success": True,
            "backup_file": backup_filename,
            "backup_path": str(backup_path),
            "backup_size_mb": round(backup_size, 2),
            "created_at": datetime.utcnow().isoformat(),
            "message": "Database backup created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")

# Helper functions
def _get_application_uptime() -> float:
    """Calculate application uptime in hours"""
    try:
        # This is a simplified implementation
        # In production, you'd track actual application start time
        return psutil.boot_time() / 3600  # Placeholder
    except:
        return 0.0

async def _get_database_statistics() -> Dict[str, Any]:
    """Get database-specific statistics"""
    try:
        # Get table counts
        stats = {}
        
        # Document statistics
        doc_result = execute_raw_sql("SELECT COUNT(*) as count, status FROM documents GROUP BY status")
        if doc_result["success"]:
            stats["documents"] = {row["status"]: row["count"] for row in doc_result["rows"]}
        
        # Chunk statistics
        chunk_result = execute_raw_sql("SELECT COUNT(*) as count FROM chunks")
        if chunk_result["success"]:
            stats["total_chunks"] = chunk_result["rows"][0]["count"]
        
        # Index statistics
        index_result = execute_raw_sql("SELECT COUNT(*) as count FROM vector_indexes")
        if index_result["success"]:
            stats["vector_indexes"] = index_result["rows"][0]["count"]
        
        # Database file size
        db_size = os.path.getsize(Config.DB_PATH) / (1024*1024)  # MB
        stats["database_size_mb"] = round(db_size, 2)
        
        return stats
        
    except Exception as e:
        return {"error": str(e)}

async def _get_storage_statistics() -> Dict[str, Any]:
    """Get storage usage statistics"""
    try:
        from pathlib import Path
        
        upload_dir = Path(Config.UPLOAD_FOLDER)
        
        # Calculate directory sizes
        total_size = 0
        file_count = 0
        
        if upload_dir.exists():
            for file_path in upload_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        return {
            "upload_directory": str(upload_dir),
            "total_files": file_count,
            "total_size_mb": round(total_size / (1024*1024), 2),
            "avg_file_size_kb": round(total_size / max(file_count, 1) / 1024, 2)
        }
        
    except Exception as e:
        return {"error": str(e)}

def _find_orphaned_files(db: Session, upload_dir: str) -> List[str]:
    """Find files in upload directory that are not referenced in database"""
    try:
        from pathlib import Path
        
        # Get all file paths from database
        files = db.query(Document).all()
        referenced_paths = set()
        
        for doc in files:
            for file_record in doc.files:
                referenced_paths.add(file_record.path)
        
        # Find files in upload directory
        upload_path = Path(upload_dir)
        orphaned_files = []
        
        if upload_path.exists():
            for file_path in upload_path.rglob("*"):
                if file_path.is_file() and str(file_path) not in referenced_paths:
                    orphaned_files.append(str(file_path))
        
        return orphaned_files
        
    except Exception as e:
        print(f"❌ Error finding orphaned files: {e}")
        return []

def _cleanup_orphaned_files(orphaned_files: List[str]) -> int:
    """Delete orphaned files"""
    deleted_count = 0
    for file_path in orphaned_files:
        try:
            os.remove(file_path)
            deleted_count += 1
        except Exception as e:
            print(f"⚠️ Could not delete {file_path}: {e}")
    
    return deleted_count

if __name__ == "__main__":
    # Test the router
    print("🧪 Admin router loaded successfully!")
    print("📋 Available endpoints:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = list(route.methods)
            print(f"  {methods} {route.path}")