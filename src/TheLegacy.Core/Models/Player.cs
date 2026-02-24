using TheLegacy.Core.Enums;

namespace TheLegacy.Core.Models;

public class Player
{
    public required string Name { get; init; }
    public int Life { get; set; } = 20;

    public Zone Library { get; init; } = new() { Type = ZoneType.Library };
    public Zone Hand { get; init; } = new() { Type = ZoneType.Hand };
    public Zone Graveyard { get; init; } = new() { Type = ZoneType.Graveyard };
}
