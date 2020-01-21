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

    collection = "data/wos_refs.ds"

    all_metadata = []
    dot_paths = [
        ".static_data.fullrecord_metadata.addresses.address_name",
        ".UID",
        ".static_data.summary.titles.title",
    ]
    labels = [
        "addresses",
        "uid",
        "titles",
    ]
    keys = dataset.keys(collection)
    keys.remove("captured")
    print("Collecting records")
    all_metadata = get_records(dot_paths, "authors", collection, keys, labels)
    # all_metadata.sort(key=lambda all_metadata: all_metadata["creator_family"])
    print("Processing Records")
    for metadata in all_metadata:
        if "addresses" in metadata:
            # print(metadata['uid'])
            caltech = False
            caltech_names = []
            JPL = False
            jpl_names = []
            for a in metadata["addresses"]:
                if type(a) is not str:
                    if "organizations" in a["address_spec"]:
                        if (
                            type(a["address_spec"]["organizations"]["organization"])
                            == list
                        ):
                            ct_internal = False
                            jpl_internal = False
                            for org in a["address_spec"]["organizations"][
                                "organization"
                            ]:
                                if "content" in org:
                                    if (
                                        org["content"]
                                        == "NASA Jet Propulsion Laboratory (JPL)"
                                    ):
                                        jpl_internal = True
                                        # print("JPL")
                                    if (
                                        org["content"]
                                        == "California Institute of Technology"
                                    ):
                                        ct_internal = True
                                        # print("Caltech")
                                else:
                                    if org == "Jet Prop Lab":
                                        # print("JPL")
                                        jpl_internal = True
                                    elif org == "CALTECH":
                                        # print("Caltech")
                                        ct_internal = True
                            if jpl_internal:
                                JPL = True
                                for name in a["names"]["name"]:
                                    print(a["names"])
                                    if "display_name" in name:
                                        jpl_names.append(name["display_name"])
                                    else:
                                        jpl_names.append(name)
                            if ct_internal and not jpl_internal:
                                caltech = True
                                for name in a["names"]["name"]:
                                    print(a["names"])
                                    if "display_name" in name:
                                        caltech_names.append(name["display_name"])
                                    else:
                                        caltech_names.append(name)
            if caltech and JPL:
                print(jpl_names)
                print(caltech_names)
                # print('Caltech ',caltech,' JPL ',JPL)
                # else:
                # print('Non-normalized org', org)
                # else:
                # print('Single org ', a['address_spec']['organizations']['organization'])
                # else:
                # print("Non-standard address format: ",a,metadata['uid'])
                # else:
                # print("Odd address format: ",a,metadata['uid'])
        # else:
        # print(metadata['uid'],' NO ADDRESSES')
