using TheLegacy.Core.Enums;

namespace TheLegacy.Core.Models;

public class GameState
{
    public List<Player> Players { get; init; } = [];
    public Zone Battlefield { get; init; } = new() { Type = ZoneType.Battlefield };
    public Zone Stack { get; init; } = new() { Type = ZoneType.Stack };
    public Zone Exile { get; init; } = new() { Type = ZoneType.Exile };

    public int TurnNumber { get; set; }
    public int ActivePlayerIndex { get; set; }
    public Player? ActivePlayer => Players.Count > ActivePlayerIndex ? Players[ActivePlayerIndex] : null;
}
