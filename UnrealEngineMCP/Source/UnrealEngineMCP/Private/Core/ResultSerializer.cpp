#include "Core/ResultSerializer.h"

FUnrealEngineMCPResponse FUnrealEngineMCPResultSerializer::Ok(const FString& Id, TSharedPtr<FJsonObject> Result, double DurationMs)
{
	FUnrealEngineMCPResponse R;
	R.Id = Id;
	R.bOk = true;
	R.Result = Result.IsValid() ? Result : MakeShared<FJsonObject>();
	R.DurationMs = DurationMs;
	return R;
}

FUnrealEngineMCPResponse FUnrealEngineMCPResultSerializer::Fail(const FString& Id, const FString& Code, const FString& Message, TSharedPtr<FJsonObject> Details, double DurationMs)
{
	FUnrealEngineMCPResponse R;
	R.Id = Id;
	R.bOk = false;
	R.ErrorCode = Code;
	R.ErrorMessage = Message;
	R.ErrorDetails = Details.IsValid() ? Details : MakeShared<FJsonObject>();
	R.DurationMs = DurationMs;
	return R;
}

TSharedPtr<FJsonObject> FUnrealEngineMCPResultSerializer::Vector(const FVector& V)
{
	TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
	O->SetNumberField(TEXT("x"), V.X);
	O->SetNumberField(TEXT("y"), V.Y);
	O->SetNumberField(TEXT("z"), V.Z);
	return O;
}

TSharedPtr<FJsonObject> FUnrealEngineMCPResultSerializer::Rotator(const FRotator& R)
{
	TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
	O->SetNumberField(TEXT("pitch"), R.Pitch);
	O->SetNumberField(TEXT("yaw"), R.Yaw);
	O->SetNumberField(TEXT("roll"), R.Roll);
	return O;
}

TSharedPtr<FJsonObject> FUnrealEngineMCPResultSerializer::Transform(const FTransform& T)
{
	TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
	O->SetObjectField(TEXT("location"), Vector(T.GetLocation()));
	O->SetObjectField(TEXT("rotation"), Rotator(T.Rotator()));
	O->SetObjectField(TEXT("scale"), Vector(T.GetScale3D()));
	return O;
}

bool FUnrealEngineMCPResultSerializer::TryGetVector(const TSharedPtr<FJsonObject>& Obj, const FString& Field, FVector& Out)
{
	if (!Obj.IsValid() || !Obj->HasTypedField<EJson::Object>(Field)) return false;
	const TSharedPtr<FJsonObject> V = Obj->GetObjectField(Field);
	Out.X = V->GetNumberField(TEXT("x"));
	Out.Y = V->GetNumberField(TEXT("y"));
	Out.Z = V->GetNumberField(TEXT("z"));
	return true;
}

bool FUnrealEngineMCPResultSerializer::TryGetRotator(const TSharedPtr<FJsonObject>& Obj, const FString& Field, FRotator& Out)
{
	if (!Obj.IsValid() || !Obj->HasTypedField<EJson::Object>(Field)) return false;
	const TSharedPtr<FJsonObject> V = Obj->GetObjectField(Field);
	Out.Pitch = V->GetNumberField(TEXT("pitch"));
	Out.Yaw = V->GetNumberField(TEXT("yaw"));
	Out.Roll = V->GetNumberField(TEXT("roll"));
	return true;
}
