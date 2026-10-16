from typing import List, Optional
from pydantic import BaseModel, Field


class NetworkFlowRecord(BaseModel):
    Destination_Port: Optional[int] = Field(default=80, alias="Destination Port")
    Flow_Duration: Optional[int] = Field(default=0, alias="Flow Duration")
    Total_Fwd_Packets: Optional[int] = Field(default=0, alias="Total Fwd Packets")
    Total_Backward_Packets: Optional[int] = Field(default=0, alias="Total Backward Packets")
    Total_Length_of_Fwd_Packets: Optional[float] = Field(
        default=0.0, alias="Total Length of Fwd Packets"
    )
    Total_Length_of_Bwd_Packets: Optional[float] = Field(
        default=0.0, alias="Total Length of Bwd Packets"
    )
    Fwd_Packet_Length_Max: Optional[float] = Field(default=0.0, alias="Fwd Packet Length Max")
    Fwd_Packet_Length_Min: Optional[float] = Field(default=0.0, alias="Fwd Packet Length Min")
    Fwd_Packet_Length_Mean: Optional[float] = Field(default=0.0, alias="Fwd Packet Length Mean")
    Flow_IAT_Mean: Optional[float] = Field(default=0.0, alias="Flow IAT Mean")
    Flow_IAT_Std: Optional[float] = Field(default=0.0, alias="Flow IAT Std")
    Flow_IAT_Max: Optional[float] = Field(default=0.0, alias="Flow IAT Max")
    FIN_Flag_Count: Optional[int] = Field(default=0, alias="FIN Flag Count")
    SYN_Flag_Count: Optional[int] = Field(default=0, alias="SYN Flag Count")
    RST_Flag_Count: Optional[int] = Field(default=0, alias="RST Flag Count")
    PSH_Flag_Count: Optional[int] = Field(default=0, alias="PSH Flag Count")
    ACK_Flag_Count: Optional[int] = Field(default=0, alias="ACK Flag Count")
    Down_Up_Ratio: Optional[float] = Field(default=0.0, alias="Down/Up Ratio")
    Average_Packet_Size: Optional[float] = Field(default=0.0, alias="Average Packet Size")

    class Config:
        populate_by_name = True


class BatchFlowRequest(BaseModel):
    flows: List[NetworkFlowRecord]


class PredictionResponse(BaseModel):
    is_malicious: bool
    label: str
    attack_family: str
    confidence: float
    severity: str
    threshold: float
    model_version: str


class BatchPredictionResponse(BaseModel):
    total_flows: int
    malicious_count: int
    benign_count: int
    predictions: List[PredictionResponse]


class ModelInfoResponse(BaseModel):
    model_name: str
    status: str
    version: str
    threshold: float
    features_count: int
    supported_families: List[str]
    trained_timestamp: Optional[str] = None
