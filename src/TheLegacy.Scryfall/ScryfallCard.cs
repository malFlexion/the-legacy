using System.Text.Json.Serialization;

namespace TheLegacy.Scryfall;

public class ScryfallCard
{
    [JsonPropertyName("id")]
    public Guid Id { get; set; }

    [JsonPropertyName("oracle_id")]
    public Guid OracleId { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("mana_cost")]
    public string? ManaCost { get; set; }

    [JsonPropertyName("cmc")]
    public decimal Cmc { get; set; }

    [JsonPropertyName("type_line")]
    public string TypeLine { get; set; } = string.Empty;

    [JsonPropertyName("oracle_text")]
    public string? OracleText { get; set; }

    [JsonPropertyName("colors")]
    public List<string>? Colors { get; set; }

    [JsonPropertyName("color_identity")]
    public List<string> ColorIdentity { get; set; } = [];

    [JsonPropertyName("keywords")]
    public List<string> Keywords { get; set; } = [];

    [JsonPropertyName("power")]
    public string? Power { get; set; }

    [JsonPropertyName("toughness")]
    public string? Toughness { get; set; }

    [JsonPropertyName("loyalty")]
    public string? Loyalty { get; set; }

    [JsonPropertyName("set")]
    public string SetCode { get; set; } = string.Empty;

    [JsonPropertyName("rarity")]
    public string Rarity { get; set; } = string.Empty;

    [JsonPropertyName("layout")]
    public string Layout { get; set; } = string.Empty;

    [JsonPropertyName("legalities")]
    public Dictionary<string, string>? Legalities { get; set; }
}
