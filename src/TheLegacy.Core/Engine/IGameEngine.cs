using TheLegacy.Core.Commands;
using TheLegacy.Core.Models;

namespace TheLegacy.Core.Engine;

public interface IGameEngine
{
    GameState Execute(GameState state, IGameCommand command);
}
