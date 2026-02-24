using TheLegacy.Core.Enums;
using TheLegacy.Scryfall;

namespace TheLegacy.Scryfall.Tests;

public class CardMapperTests
{
    [Fact]
    public void ToCard_Creature_MapsAllFields()
    {
        var scryfall = new ScryfallCard
        {
            OracleId = Guid.NewGuid(),
            Name = "Grizzly Bears",
            ManaCost = "{1}{G}",
            Cmc = 2,
            TypeLine = "Creature — Bear",
            OracleText = "",
            Colors = ["G"],
            ColorIdentity = ["G"],
            Keywords = [],
            Power = "2",
            Toughness = "2",
            Rarity = "common",
            SetCode = "lea",
            Layout = "normal",
        };

        var card = CardMapper.ToCard(scryfall);

        Assert.Equal("Grizzly Bears", card.Name);
        Assert.Equal(Color.Green, card.Colors);
        Assert.Equal(CardType.Creature, card.Types);
        Assert.Equal(Supertype.None, card.Supertypes);
        Assert.Equal(["Bear"], card.Subtypes);
        Assert.Equal("2", card.Power);
        Assert.Equal("2", card.Toughness);
        Assert.Equal(2, card.ManaCost.ConvertedManaCost);
    }

    [Fact]
    public void ToCard_LegendaryCreature_ParsesSupertypeAndSubtypes()
    {
        var scryfall = new ScryfallCard
        {
            OracleId = Guid.NewGuid(),
            Name = "Thalia, Guardian of Thraben",
            ManaCost = "{1}{W}",
            Cmc = 2,
            TypeLine = "Legendary Creature — Human Soldier",
            Colors = ["W"],
            ColorIdentity = ["W"],
            Rarity = "rare",
            Layout = "normal",
        };

        var card = CardMapper.ToCard(scryfall);

        Assert.Equal(Supertype.Legendary, card.Supertypes);
        Assert.Equal(CardType.Creature, card.Types);
        Assert.Equal(new[] { "Human", "Soldier" }, card.Subtypes);
    }

    [Fact]
    public void ToCard_Instant_HasNoSubtypes()
    {
        var scryfall = new ScryfallCard
        {
            OracleId = Guid.NewGuid(),
            Name = "Lightning Bolt",
            ManaCost = "{R}",
            Cmc = 1,
            TypeLine = "Instant",
            OracleText = "Lightning Bolt deals 3 damage to any target.",
            Colors = ["R"],
            ColorIdentity = ["R"],
            Rarity = "common",
            Layout = "normal",
        };

        var card = CardMapper.ToCard(scryfall);

        Assert.Equal(CardType.Instant, card.Types);
        Assert.Empty(card.Subtypes);
        Assert.Equal(1, card.ManaCost.ConvertedManaCost);
    }
}
