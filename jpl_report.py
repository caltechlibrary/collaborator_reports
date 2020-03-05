import csv
from py_dataset import dataset


def get_records(dot_paths, f_name, d_name, keys, labels=None):
    if dataset.has_frame(d_name, f_name):
        dataset.delete_frame(d_name, f_name)
    if labels:
        f, err = dataset.frame(d_name, f_name, keys, dot_paths, labels)
        if err != "":
            print(f"ERROR: Can't create {f_name} in {d_name}, {err}")
    else:
        # If labels arn't provided, just base on dot path
        labels = []
        for d in dot_paths:
            labels.append(d.split(".")[-1])
        f, err = dataset.frame(d_name, f_name, keys, dot_paths, labels)
        if err != "":
            print(f"ERROR: Can't create {f_name} in {d_name}, {err}")
    return dataset.frame_objects(d_name, f_name)


if __name__ == "__main__":

    report = "jpl_report.csv"

    collaborative = 0
    caltech_only = 0
    jpl_only = 0

    with open(report, "w", newline="\n", encoding="utf-8") as fout:
        file_out = csv.writer(fout)
        file_out.writerow(
            [
                "uid",
                "title",
                "journal",
                "jpl authors",
                "caltech authors",
                "publication date",
                "jpl_order",
                "caltech_order"
            ]
        )

        collection = "data/wos_refs.ds"

        all_metadata = []
        dot_paths = [
            ".static_data.fullrecord_metadata.addresses.address_name",
            ".UID",
            ".static_data.summary.titles.title",
            ".static_data.summary.pub_info.sortdate",
        ]
        labels = ["addresses", "uid", "titles", "sortdate"]
        keys = dataset.keys(collection)
        keys.remove("captured")
        print("Collecting records")
        all_metadata = get_records(dot_paths, "authors", collection, keys, labels)
        all_metadata.sort(key=lambda all_metadata: all_metadata["sortdate"])
        print("Processing Records")
        for metadata in all_metadata:
            if "addresses" in metadata:
                caltech = False
                caltech_names = []
                caltech_order = []
                JPL = False
                jpl_names = []
                jpl_order = []
                for a in metadata["addresses"]:
                    if type(a) is not str:
                        spec = a["address_spec"]
                        if "organizations" in spec:
                            if type(spec["organizations"]["organization"]) == list:
                                ct_internal = False
                                jpl_internal = False
                                for org in spec["organizations"]["organization"]:
                                    if "content" in org:
                                        if (
                                            org["content"]
                                            == "NASA Jet Propulsion Laboratory (JPL)"
                                        ):
                                            jpl_internal = True
                                        if (
                                            org["content"]
                                            == "California Institute of Technology"
                                        ):
                                            if "zip" in spec:
                                                if (
                                                    a["address_spec"]["zip"]["content"]
                                                    != 91109
                                                ):
                                                    ct_internal = True
                                            else:
                                                ct_internal = True
                                    else:
                                        if org == "Jet Prop Lab":
                                            jpl_internal = True
                                        elif org == "CALTECH":
                                            if "zip" in spec:
                                                if spec["zip"]["content"] != 91109:
                                                    ct_internal = True
                                            else:
                                                ct_internal = True
                                if jpl_internal:
                                    JPL = True
                                    if "names" in a:
                                        if type(a["names"]["name"]) == list:
                                            for name in a["names"]["name"]:
                                                if "display_name" in name:
                                                    jpl_names.append(
                                                        name["display_name"]
                                                    )
                                                    jpl_order.append(name["seq_no"])
                                        else:
                                            name = a["names"]["name"]
                                            jpl_names.append(
                                                name["display_name"]
                                            )
                                            jpl_order.append(name["seq_no"])
                                if ct_internal and not jpl_internal:
                                    caltech = True
                                    if "names" in a:
                                        if type(a["names"]["name"]) == list:
                                            for name in a["names"]["name"]:
                                                if "display_name" in name:
                                                    caltech_names.append(
                                                        name["display_name"]
                                                    )
                                                    caltech_order.append(name["seq_no"])
                                        else:
                                            name = a["names"]["name"]
                                            caltech_names.append(
                                                name["display_name"]
                                            )
                                            caltech_order.append(name["seq_no"])
                if caltech and JPL:
                    collaborative = collaborative + 1
                    title = ""
                    journal = ""
                    for t in metadata["titles"]:
                        if t["type"] == "item":
                            title = t["content"]
                        if t["type"] == "source":
                            journal = t["content"]
                    file_out.writerow(
                        [
                            metadata["uid"],
                            title,
                            journal,
                            jpl_names,
                            caltech_names,
                            metadata["sortdate"],
                            jpl_order,
                            caltech_order
                        ]
                    )
                if JPL and not caltech:
                    jpl_only = jpl_only + 1
                if caltech and not JPL:
                    caltech_only = caltech_only + 1

    print(f'Caltech:{caltech_only} JPL:{jpl_only} Collaborative:{collaborative}')

