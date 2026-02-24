using System.Text.Json;

namespace TheLegacy.Scryfall;

public class BulkDataProvider
{
    private readonly ScryfallClient _client;
    private readonly string _cacheDirectory;

    public BulkDataProvider(ScryfallClient client, string? cacheDirectory = null)
    {
        _client = client;
        _cacheDirectory = cacheDirectory ?? Path.Combine(AppContext.BaseDirectory, "data");
    }

    public async Task<IReadOnlyList<ScryfallCard>> GetOracleCardsAsync(CancellationToken ct = default)
    {
        var cacheFile = Path.Combine(_cacheDirectory, "oracle-cards.json");
        var metaFile = Path.Combine(_cacheDirectory, "oracle-cards.meta");

        var bulkInfo = await _client.GetBulkDataInfoAsync("oracle_cards", ct);

        if (!NeedsRefresh(metaFile, bulkInfo.UpdatedAt))
        {
            Console.WriteLine("Using cached card data.");
            return await LoadFromCacheAsync(cacheFile, ct);
        }

        Console.WriteLine($"Downloading oracle cards ({bulkInfo.Size / 1_048_576}MB)...");
        await _client.DownloadFileAsync(bulkInfo.DownloadUri, cacheFile, ct);
        await File.WriteAllTextAsync(metaFile, bulkInfo.UpdatedAt.ToString("O"), ct);
        Console.WriteLine("Download complete.");

        return await LoadFromCacheAsync(cacheFile, ct);
    }

    private static bool NeedsRefresh(string metaFile, DateTimeOffset remoteUpdatedAt)
    {
        if (!File.Exists(metaFile))
            return true;

        var cachedTimestamp = File.ReadAllText(metaFile).Trim();
        if (!DateTimeOffset.TryParse(cachedTimestamp, out var cachedDate))
            return true;

        return remoteUpdatedAt > cachedDate;
    }

    private static async Task<IReadOnlyList<ScryfallCard>> LoadFromCacheAsync(string cacheFile, CancellationToken ct)
    {
        Console.WriteLine("Loading cards from cache...");
        await using var stream = File.OpenRead(cacheFile);
        var cards = await JsonSerializer.DeserializeAsync<List<ScryfallCard>>(stream, cancellationToken: ct)
            ?? throw new InvalidOperationException("Failed to deserialize card data.");
        Console.WriteLine($"Loaded {cards.Count:N0} cards.");
        return cards;
    }
}
