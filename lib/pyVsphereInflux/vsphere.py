"""Tools for connecting to vsphere and collecting data"""

from pyVmomi import vim
from pyVsphereInflux import InfluxResult
from pyVsphereInflux.tools import pchelper

def build_vmresultset(service_instance, tags, fields, measurement='vmprop'):
    """Build a list of InfluxResult objects
            Arguments:
                service_instance: a service instance as returned from
                                  pyvim.connect.smartconnect
                tags: a list of VM properties to use as Influx tags
                fields: a list of VM propertries to use as Influx fields
                measurement: the influx db measurement name to use
            Results:
                A list of InfluxResult objects suitable to insert into a 
                database.
    """
    res = []

    root_folders = service_instance.content.rootFolder.childEntity
    for child in root_folders:
        if hasattr(child, 'vmFolder'):
            datacenter = child
        else: 
            continue

        dc_children = get_vms(service_instance, datacenter.vmFolder, 
                              "", tags, fields, measurement)

        for dc_child in dc_children:
            dc_child.tags['datacenter'] = datacenter.name
        res.extend(dc_children)


    return res

def get_vms(service_instance, folder, parent_path, tags, fields, measurement):
    """Returns a list of InfluxResult objects representing the child objects
       of vm_or_folder
            Arguments:
                service_instance: a service instance as returned from
                                  pyVim.connect.SmartConnect
                vm_or_folder: the root of the VM/folder tree to search
                parent_path: the path of parent of vm_or_folder
                tags: a list of VM properties to use as Influx tags
                fields: a list of VM propertries to use as Influx fields
                measurement: the influx db measurement name to use
            Results:
                A list of InfluxResult objects suitable to insert into a 
                database.
    """
    res = []

    # collect child folders
    #print parent_path
    folder_spec = pchelper.get_container_view(service_instance, 
                                              obj_type=[vim.Folder],
                                              container=folder,
                                              recursive=False)
    folders = pchelper.collect_properties(service_instance, 
                                          view_ref=folder_spec,
                                          obj_type=vim.Folder,
                                          path_set=['name'],
                                          include_mors=True)
    for child_folder in folders:
        child_vms = get_vms(service_instance, child_folder['obj'], 
                            "%s/%s" % (parent_path, child_folder['obj'].name),
                             tags, fields, measurement)
        res.extend(child_vms)
                                     

    # collect child vms
    props = []
    props.extend(tags)
    props.extend(fields)
    vm_spec = pchelper.get_container_view(service_instance, 
                                          obj_type=[vim.VirtualMachine],
                                          container=folder,
                                          recursive=False)
    vms = pchelper.collect_properties(service_instance, view_ref=vm_spec,
                                      obj_type=vim.VirtualMachine,
                                      path_set=props,
                                      include_mors=False)

    # put each child into res
    for vm in vms:
        ts = InfluxResult(measurement)
        for tag in tags:
            ts.tags[tag] = vm[tag]
        for field in fields:
            ts.fields[field] = vm[field]
        ts.tags['folderPath'] = parent_path
        res.append(ts)

    return res 

# vim: et:ai:sw=4:ts=4
