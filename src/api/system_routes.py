from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Dict, Any, Annotated
import subprocess
import logging

from src.models.database import User, get_db
from src.services.auth_service import AuthService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.get(
    "/system/gpu",
    response_model=Dict[str, Any],
    summary="Get GPU information",
    description="Returns GPU information including availability, models, and VRAM",
    tags=["System"],
)
async def get_gpu_info(current_user: User = Depends(get_current_user)):
    """Get GPU information for the system (supports NVIDIA and AMD)."""
    # Try NVIDIA first
    nvidia_info = _get_nvidia_gpu_info()
    if nvidia_info["available"]:
        return nvidia_info
    
    # Try AMD if NVIDIA not found
    amd_info = _get_amd_gpu_info()
    if amd_info["available"]:
        return amd_info
    
    # No GPU detected
    return {
        "available": False,
        "message": "No GPU detected (checked NVIDIA and AMD)",
        "gpu_count": 0,
        "gpus": []
    }


def _get_nvidia_gpu_info() -> Dict[str, Any]:
    """Get NVIDIA GPU information via nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            gpus = []
            
            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    gpus.append({
                        "name": parts[0],
                        "type": "NVIDIA",
                        "memory_total_mb": float(parts[1]),
                        "memory_used_mb": float(parts[2]),
                        "memory_free_mb": float(parts[3]),
                        "utilization_percent": float(parts[4])
                    })
            
            return {
                "available": True,
                "gpu_type": "NVIDIA",
                "gpu_count": len(gpus),
                "gpus": gpus,
                "driver_version": _get_nvidia_driver_version()
            }
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"NVIDIA GPU not detected: {e}")
    
    return {"available": False, "gpu_count": 0, "gpus": []}


def _get_amd_gpu_info() -> Dict[str, Any]:
    """Get AMD GPU information via rocm-smi."""
    try:
        # Try rocm-smi for AMD GPUs
        result = subprocess.run(
            ["rocm-smi", "--showuse", "--showmeminfo", "vram"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            # Parse rocm-smi output (basic parsing)
            gpus = []
            lines = result.stdout.strip().split('\n')
            
            # This is a simplified parser - rocm-smi output varies
            gpu_name = "AMD GPU"
            for line in lines:
                if "GPU" in line and ":" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        gpu_name = parts[1].strip()
                        break
            
            gpus.append({
                "name": gpu_name,
                "type": "AMD",
                "memory_total_mb": 0,  # rocm-smi parsing needed
                "memory_used_mb": 0,
                "memory_free_mb": 0,
                "utilization_percent": 0
            })
            
            return {
                "available": True,
                "gpu_type": "AMD",
                "gpu_count": len(gpus),
                "gpus": gpus,
                "driver_version": "ROCm"
            }
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"AMD GPU not detected: {e}")
    
    return {"available": False, "gpu_count": 0, "gpus": []}


def _get_nvidia_driver_version() -> str:
    """Get NVIDIA driver version."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return "Unknown"
