class Protocol(object):
    ValidOps = ["and", "or"]
    ValidHiliteModes = ["hilite", "unhilite", "toggle", "clear"]

    @staticmethod
    def simple(operator, *wheres, **attributes):
        """
        Builds a simple where clause for the hilite command

        :param wheres: a list of finished where sub clauses
        :param attributes: the attributes and their values to be added
        :returns: the where dict

        e.g.
        simple("and", ilastik_id=42, time=1337)
            => WHERE ( ilastik_id == 42 AND time == 1337 )
        """
        operands = list(wheres)
        for name, value in attributes.iteritems():
            operands.append({
                "operator": "==",
                "row": name,
                "value": value
            })

        return {
            "operator": operator,
            "operands": operands
        }

    @staticmethod
    def simple_in(row, possibilities):
        """
        Builds a simple where clause ( using 'in' ) for the hilite command

        :param row: the row name that must be in possibilities
        :param possibilities: the possible values row can have
        :returns: the where dict

        e.g.
        simple("track_id1", [42, 1337, 12345])
            => WHERE ( track_id1 == 42 OR track_id1 == 1337 OR track_id1 == 12345 )
        """
        operands = []
        for p in possibilities:
            operands.append({
                "operator": "==",
                "row": row,
                "value": p,
            })

        return {
            "operator": "or",
            "operands": operands
        }

    @staticmethod
    def clear():
        """
        Builds the clear hilite command to clear all hilites
        :returns: the command dict
        """
        return {
            "command": "hilite",
            "mode": "clear",
        }

    @staticmethod
    def cmd(mode, where=None):
        if mode.lower() not in Protocol.ValidHiliteModes:
            raise ValueError("Mode '{}' not supported".format(mode))
        command = {
            "command": "hilite",
            "mode": mode
        }
        if where is not None:
            command["where"] = where
        return command

    @staticmethod
    def verbose(command):
        """
        returns the command in an SQL like readable form

        :param command: the command to convert
        :type command: dict
        :returns: the command as str
        """
        assert "command" in command, "Must be a command dict"
        assert command["command"] == "hilite", "Only hilite commands supported"

        mode = command["mode"]
        if mode == "clear":
            return "CLEAR *"
        where = []
        Protocol._parse(where, command["where"])

        return "{} * WHERE {}".format(mode.upper(), " ".join(where))

    @staticmethod
    def _parse(where, sub):
        if "operand" in sub:
            where.append(sub["operator"].upper())
            where.append("(")
            Protocol._parse(where, sub["operand"])
            where.append(")")
        elif "operands" in sub:
            if not sub["operands"]:
                where.append("MISSING")
                where.append(None)
            for operand in sub["operands"]:
                where.append("(")
                Protocol._parse(where, operand)
                where.append(")")
                where.append(sub["operator"].upper())
            where.pop()
        else:
            where.append(sub["row"])
            where.append(sub["operator"].upper())
            where.append(str(sub["value"]))
