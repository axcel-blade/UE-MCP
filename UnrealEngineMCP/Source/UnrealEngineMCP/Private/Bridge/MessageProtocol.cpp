#include "Bridge/MessageProtocol.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

bool FUnrealEngineMCPMessageProtocol::TryParseRequest(const TArray<uint8>& Body, FUnrealEngineMCPRequest& OutRequest, FString& OutError)
{
	FString JsonString;
	FFileHelper::BufferToString(JsonString, Body.GetData(), Body.Num());
	TSharedPtr<FJsonObject> Root;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		OutError = TEXT("Invalid JSON");
		return false;
	}
	OutRequest.Id = Root->GetStringField(TEXT("id"));
	OutRequest.Version = Root->HasField(TEXT("version")) ? Root->GetStringField(TEXT("version")) : ProtocolVersion;
	OutRequest.Method = Root->GetStringField(TEXT("method"));
	OutRequest.Params = Root->HasTypedField<EJson::Object>(TEXT("params")) ? Root->GetObjectField(TEXT("params")) : MakeShared<FJsonObject>();
	OutRequest.Auth = Root->HasField(TEXT("auth")) ? Root->GetStringField(TEXT("auth")) : FString();
	if (OutRequest.Method.IsEmpty())
	{
		OutError = TEXT("Missing method");
		return false;
	}
	return true;
}

TArray<uint8> FUnrealEngineMCPMessageProtocol::EncodeResponse(const FUnrealEngineMCPResponse& Response)
{
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("id"), Response.Id);
	Root->SetBoolField(TEXT("ok"), Response.bOk);
	Root->SetNumberField(TEXT("duration_ms"), Response.DurationMs);
	if (Response.bOk)
	{
		Root->SetObjectField(TEXT("result"), Response.Result.IsValid() ? Response.Result : MakeShared<FJsonObject>());
	}
	else
	{
		TSharedPtr<FJsonObject> Err = MakeShared<FJsonObject>();
		Err->SetStringField(TEXT("code"), Response.ErrorCode);
		Err->SetStringField(TEXT("message"), Response.ErrorMessage);
		Err->SetObjectField(TEXT("details"), Response.ErrorDetails.IsValid() ? Response.ErrorDetails : MakeShared<FJsonObject>());
		Root->SetObjectField(TEXT("error"), Err);
	}
	if (!Response.AsyncJobId.IsEmpty())
	{
		Root->SetStringField(TEXT("async_job_id"), Response.AsyncJobId);
	}

	FString Out;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Out);
	FJsonSerializer::Serialize(Root.ToSharedRef(), Writer);
	FTCHARToUTF8 Converter(*Out);
	TArray<uint8> Bytes;
	Bytes.Append(reinterpret_cast<const uint8*>(Converter.Get()), Converter.Length());
	return EncodeFrame(Bytes);
}

TArray<uint8> FUnrealEngineMCPMessageProtocol::EncodeFrame(const TArray<uint8>& JsonBody)
{
	TArray<uint8> Frame;
	const uint32 Len = static_cast<uint32>(JsonBody.Num());
	Frame.Add((Len >> 24) & 0xFF);
	Frame.Add((Len >> 16) & 0xFF);
	Frame.Add((Len >> 8) & 0xFF);
	Frame.Add(Len & 0xFF);
	Frame.Append(JsonBody);
	return Frame;
}

bool FUnrealEngineMCPMessageProtocol::TryReadLength(const uint8* Data, int32 Len, uint32& OutLength)
{
	if (Len < 4) return false;
	OutLength = (uint32(Data[0]) << 24) | (uint32(Data[1]) << 16) | (uint32(Data[2]) << 8) | uint32(Data[3]);
	return OutLength <= MaxMessageBytes;
}
