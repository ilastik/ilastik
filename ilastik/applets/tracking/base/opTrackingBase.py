from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.rtype import SubRegion, List
from lazyflow.stype import Opaque

import numpy as np
import pgmlink
from ilastik.applets.tracking.base.trackingUtilities import relabel
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key
from ilastik.applets.objectExtraction import config


class OpTrackingBase(Operator):
    name = "Tracking"
    category = "other"

    LabelImage = InputSlot()
    ObjectFeatures = InputSlot(stype=Opaque, rtype=List)    
    RawImage = InputSlot()
    Parameters = InputSlot( value={} ) 

    Output = OutputSlot()    
    
    def __init__(self, parent=None, graph=None):
        super(OpTrackingBase, self).__init__(parent=parent, graph=graph)        
        self.label2color = []  
    
    def setupOutputs(self):        
        self.Output.meta.assignFrom(self.LabelImage.meta)        
    
    def execute(self, slot, subindex, roi, result):
        if slot is self.Output:
            result = self.LabelImage.get(roi).wait()
            if not self.Parameters.ready():
                raise Exception("Parameter slot is not ready")        
            parameters = self.Parameters.value
            
            t_start = roi.start[0]
            t_end = roi.stop[0]
            for t in range(t_start, t_end):
                if ('time_range' in parameters and t <= parameters['time_range'][-1] and t >= parameters['time_range'][0]):                
                    result[t-t_start, ..., 0] = relabel(result[t-t_start, ..., 0], self.label2color[t])
                else:
                    result[t-t_start,...] = 0
            return result          
        
    def propagateDirty(self, inputSlot, subindex, roi):     
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)

    def _setLabel2Color(self, events, time_range, filtered_labels, x_range, y_range, z_range, successive_ids=True):        
        label2color = []
        label2color.append({})
        mergers = []
        mergers.append({})
        
        maxId = 1 #  misdetections have id 1

        # handle start time offsets
        for i in range(time_range[0]):            
            label2color.append({})
            mergers.append({})

        for i, events_at in enumerate(self.events):
            dis = []
            app = []
            div = []
            mov = []
            merger = []            
            multi = []
            for event in events_at:
                if event.type == pgmlink.EventType.Appearance:
                    app.append((event.traxel_ids[0], event.energy))
                if event.type == pgmlink.EventType.Disappearance:
                    dis.append((event.traxel_ids[0], event.energy))
                if event.type == pgmlink.EventType.Division:
                    div.append((event.traxel_ids[0], event.traxel_ids[1], event.traxel_ids[2], event.energy))
                if event.type == pgmlink.EventType.Move:
                    mov.append((event.traxel_ids[0], event.traxel_ids[1], event.energy))
                if hasattr(pgmlink.EventType, "Merger") and event.type == pgmlink.EventType.Merger:                    
                    merger.append((event.traxel_ids[0], event.traxel_ids[1], event.energy))
                if hasattr(pgmlink.EventType, "MultiFrameMove") and event.type == pgmlink.EventType.MultiFrameMove:
                    multi.append((event.traxel_ids[0], event.traxel_ids[1], event.traxel_ids[2], event.energy))                              

            print len(dis), "dis at", i + time_range[0]
            print len(app), "app at", i + time_range[0]
            print len(div), "div at", i + time_range[0]
            print len(mov), "mov at", i + time_range[0]
            print len(merger), "merger at", i + time_range[0]
            print len(multi), "multiMoves at", i + time_range[0]
            print
            
            label2color.append({})
            mergers.append({})
                        
            for e in app:
                if successive_ids:
                    label2color[-1][e[0]] = maxId
                    maxId += 1
                else:
                    label2color[-1][e[0]] = np.random.randint(1, 255)

            for e in mov:                
                if not label2color[-2].has_key(e[0]):
                    if successive_ids:
                        label2color[-2][e[0]] = maxId
                        maxId += 1
                    else:
                        label2color[-2][e[0]] = np.random.randint(1, 255)
                label2color[-1][e[1]] = label2color[-2][e[0]]

            for e in div:
                if not label2color[-2].has_key(e[0]):
                    if successive_ids:
                        label2color[-2][e[0]] = maxId
                        maxId += 1
                    else:
                        label2color[-2][e[0]] = np.random.randint(1, 255)
                ancestor_color = label2color[-2][e[0]]
                label2color[-1][e[1]] = ancestor_color
                label2color[-1][e[2]] = ancestor_color
            
            for e in merger:
                mergers[-1][e[0]] = e[1]

            for e in multi:
                if not label2color[e[2]].has_key(e[0]):
                    if successive_ids:
                        label2color[e[2]][e[0]] = maxId
                        maxId += 1
                    else:
                        label2color[e[2]][e[0]] = np.random.randint(1, 255)
                label2color[-1][e[1]] = label2color[e[2]][e[0]]
                
        # mark the filtered objects
        for t in filtered_labels.keys():
            fl_at = filtered_labels[t]
            for l in fl_at:
                assert(l not in label2color[int(t)])
                label2color[int(t)][l] = 0                

        self.label2color = label2color
        self.mergers = mergers        
        
        self.Output._value = None
        self.Output.setDirty(slice(None))
        

    def _generate_traxelstore(self,
                               time_range,
                               x_range,
                               y_range,
                               z_range,
                               size_range,
                               x_scale=1.0,
                               y_scale=1.0,
                               z_scale=1.0,
                               with_div=False,
                               with_local_centers=False,
                               median_object_size=None,
                               max_traxel_id_at=None,
                               with_opt_correction=False,
                               with_coordinate_list=False,
                               with_classifier_prior=False):
                
        if not self.Parameters.ready():
            raise Exception("Parameter slot is not ready")
        
        parameters = self.Parameters.value
        parameters['scales'] = [x_scale,y_scale,z_scale] 
        parameters['time_range'] = [min(time_range),max(time_range)]
        parameters['x_range'] = x_range
        parameters['y_range'] = y_range
        parameters['z_range'] = z_range
        parameters['size_range'] = size_range
        self.Parameters.setValue(parameters)
        
        print "generating traxels"
        print "fetching region features and division probabilities"
        feats = self.ObjectFeatures(time_range).wait()        
        
        if with_div:
            divProbs = self.DivisionProbabilities(time_range).wait()
        
        if with_local_centers:
            localCenters = self.RegionLocalCenters(time_range).wait()
        
        if with_classifier_prior:
            detProbs = self.DetectionProbabilities(time_range).wait()
            
        print "filling traxelstore"
        ts = pgmlink.TraxelStore()
                
        max_traxel_id_at = pgmlink.VectorOfInt()  
        filtered_labels = {}        
        obj_sizes = []
        total_count = 0
        empty_frame = False
        for t in feats.keys():
            rc = feats[t][default_features_key]['RegionCenter']
            if rc.size:
                rc = rc[1:, ...]
                
            if with_opt_correction:
                try:
                    rc_corr = feats[t][config.features_vigra_name]['RegionCenter_corr']
                except:
                    raise Exception, 'cannot consider optical correction since it has not been computed before'
                if rc_corr.size:
                    rc_corr = rc_corr[1:,...]

            ct = feats[t][default_features_key]['Count']
            if ct.size:
                ct = ct[1:, ...]

            if with_coordinate_list:
                coordinates = feats[t][config.features_vigra_name]['Coord<ValueList>']
                if len(coordinates):
                    coordinates = coordinates[1:]
                
            print "at timestep ", t, rc.shape[0], "traxels found"
            count = 0
            filtered_labels[t] = []
            for idx in range(rc.shape[0]):

                x, y, z = rc[idx]
                size = ct[idx]
                if (x < x_range[0] or x >= x_range[1] or
                    y < y_range[0] or y >= y_range[1] or
                    z < z_range[0] or z >= z_range[1] or
                    size < size_range[0] or size >= size_range[1]):
                    filtered_labels[t].append(int(idx + 1))
                    continue
                else:
                    count += 1
                tr = pgmlink.Traxel()
                tr.set_x_scale(x_scale)
                tr.set_y_scale(y_scale)
                tr.set_z_scale(z_scale)
                tr.Id = int(idx + 1)
                tr.Timestep = t

                tr.add_feature_array("com", len(rc[idx]))                
                for i, v in enumerate(rc[idx]):
                    tr.set_feature_value('com', i, float(v))

                if with_opt_correction:
                    tr.add_feature_array("com_corrected", len(rc_corr[idx]))
                    for i, v in enumerate(rc_corr[idx]):
                        tr.set_feature_value("com_corrected", i, float(v))

                if with_div:
                    tr.add_feature_array("divProb", 1)
                    # idx+1 because rc and ct start from 1, divProbs starts from 0
                    tr.set_feature_value("divProb", 0, float(divProbs[t][idx+1][1]))

                if with_classifier_prior:
                    tr.add_feature_array("detProb", len(detProbs[t][idx+1]))
                    for i, v in enumerate(detProbs[t][idx+1]):
                        val = float(v)
                        if val < 0.01:
                            val = 0.01
                        if val > 0.95:
                            val = 0.95
                        tr.set_feature_value("detProb", i, float(v))
                        
                if with_local_centers:
                    tr.add_feature_array("localCentersX", len(localCenters[t][idx+1]))  
                    tr.add_feature_array("localCentersY", len(localCenters[t][idx+1]))
                    tr.add_feature_array("localCentersZ", len(localCenters[t][idx+1]))            
                    for i, v in enumerate(localCenters[t][idx+1]):
                        tr.set_feature_value("localCentersX", i, float(v[0]))
                        tr.set_feature_value("localCentersY", i, float(v[1]))
                        tr.set_feature_value("localCentersZ", i, float(v[2]))                

                tr.add_feature_array("count", 1)
                tr.set_feature_value("count", 0, float(size))
                if median_object_size is not None:
                    obj_sizes.append(float(size))

                if with_coordinate_list:
                    tr.add_feature_array("coordinates", 3*len(coordinates[idx][0]))

                    for i, v in enumerate(coordinates[idx][0]):
                        tr.set_feature_value("coordinates", 3*i,   float(v[0]))
                        tr.set_feature_value("coordinates", 3*i+1, float(v[1]))
                        tr.set_feature_value("coordinates", 3*i+2, float(v[2]))

                    
                ts.add(tr)   
                         
            print "at timestep ", t, count, "traxels passed filter"
            max_traxel_id_at.append(int(rc.shape[0]))
            if count == 0:
                empty_frame = True
                
            total_count += count
        
        if median_object_size is not None:
            median_object_size[0] = np.median(np.array(obj_sizes),overwrite_input=True)
            print 'median object size = ' + str(median_object_size[0])
        
        return ts, filtered_labels, empty_frame
