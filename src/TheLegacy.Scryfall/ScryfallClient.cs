using System.Text.Json;

namespace TheLegacy.Scryfall;

public class ScryfallClient : IDisposable
{
    private static readonly Uri BaseUri = new("https://api.scryfall.com/");
    private readonly HttpClient _http;

    public ScryfallClient(HttpClient? httpClient = null)
    {
        _http = httpClient ?? new HttpClient();
        _http.BaseAddress = BaseUri;
        _http.DefaultRequestHeaders.UserAgent.ParseAdd("TheLegacy/0.1");
        _http.DefaultRequestHeaders.Accept.ParseAdd("application/json");
    }

    public async Task<BulkDataInfo> GetBulkDataInfoAsync(string type = "oracle_cards", CancellationToken ct = default)
    {
        var response = await _http.GetAsync("bulk-data", ct);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync(ct);
        var bulkDataList = JsonSerializer.Deserialize<BulkDataListResponse>(json)
            ?? throw new InvalidOperationException("Failed to deserialize bulk data list.");

        var entry = bulkDataList.Data.FirstOrDefault(d => d.Type == type)
            ?? throw new InvalidOperationException($"Bulk data type '{type}' not found.");

        return entry;
    }

    public async Task DownloadFileAsync(string uri, string destinationPath, CancellationToken ct = default)
    {
        using var response = await _http.GetAsync(uri, HttpCompletionOption.ResponseHeadersRead, ct);
        response.EnsureSuccessStatusCode();

        var directory = Path.GetDirectoryName(destinationPath);
        if (!string.IsNullOrEmpty(directory))
            Directory.CreateDirectory(directory);

        await using var fileStream = File.Create(destinationPath);
        await response.Content.CopyToAsync(fileStream, ct);
    }

    public void Dispose() => _http.Dispose();
}

public class BulkDataListResponse
{
    [System.Text.Json.Serialization.JsonPropertyName("data")]
    public List<BulkDataInfo> Data { get; set; } = [];
}

public class BulkDataInfo
{
    [System.Text.Json.Serialization.JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    [System.Text.Json.Serialization.JsonPropertyName("updated_at")]
    public DateTimeOffset UpdatedAt { get; set; }

    [System.Text.Json.Serialization.JsonPropertyName("download_uri")]
    public string DownloadUri { get; set; } = string.Empty;

    [System.Text.Json.Serialization.JsonPropertyName("size")]
    public long Size { get; set; }
}
