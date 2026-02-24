using TheLegacy.Core.Enums;

namespace TheLegacy.Core.Models;

public class Zone
{
    public ZoneType Type { get; init; }
    public List<Card> Cards { get; init; } = [];

    public int Count => Cards.Count;
}
