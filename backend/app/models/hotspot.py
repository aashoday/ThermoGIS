import uuid
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.database import Base

class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False)          # 'VIIRS' or 'MODIS'
    acquired_at = Column(DateTime, nullable=False)    # satellite pass timestamp
    frp = Column(Float, nullable=True)                # fire radiative power (MW)
    confidence = Column(String, nullable=True)        # source-reported confidence (nominal/low/high)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    # filled in later by processing/ML steps
    nearest_asset_id = Column(UUID(as_uuid=True), nullable=True)
    distance_to_asset_m = Column(Float, nullable=True)
    landcover_class = Column(String, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    predicted_class = Column(String, nullable=True)   # 'industrial_flare', 'crop_burn', 'wildfire'
    prediction_confidence = Column(Float, nullable=True)