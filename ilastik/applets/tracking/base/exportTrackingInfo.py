import pprint

pp = pprint.PrettyPrinter(indent=4).pprint


def export_to_csv(fname, tracking_ids, extra_ids, settings=None):
    max_objs = settings["maxObj"]
    pp(extra_ids)
    with open(fname, "w") as fout:
        fout.write("object id,ilastik_id,time")
        print max_objs
        for i in xrange(1, max_objs+1):
            fout.write(",track_id%i" % i)
        fout.write("\n")
        oid = 1
        for t, tracks in enumerate(tracking_ids):
            for ilastik_id, track_id in tracks.iteritems():
                fout.write("%i,%i,%i,%i" % (oid, ilastik_id, t, track_id))
                for i in xrange(0, max_objs - 1):
                    try:
                        eid = extra_ids[t][ilastik_id][i]
                    except (IndexError, KeyError):
                        eid = 0
                    fout.write(",%i" % eid)
                fout.write("\n")
                oid += 1
    print "exported"