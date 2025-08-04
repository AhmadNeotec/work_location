frappe.ui.form.on('Employee Checkin', {
    work_location: function(frm) {
        console.log("Work location changed:", frm.doc.work_location);
        
        if (!frm.doc.work_location) {
            // Clear fields if no work location selected
            frm.set_value('current_lat', null);
            frm.set_value('current_lng', null);
            frm.remove_location_display();
            return;
        }

        // Fetch work location details and use its coordinates
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Work Location",
                name: frm.doc.work_location
            },
            callback: function(r) {
                console.log("Work Location data:", r.message);
                
                if (r.message) {
                    const loc = r.message;
                    
                    // Check if location has required fields
                    if (!loc.latitude || !loc.longitude) {
                        frappe.msgprint({
                            title: __('Missing Data'),
                            message: __('Work Location does not have latitude/longitude configured.'),
                            indicator: 'orange'
                        });
                        return;
                    }
                    
                    // Set the work location's coordinates as current location
                    frm.set_value('current_lat', parseFloat(loc.latitude));
                    frm.set_value('current_lng', parseFloat(loc.longitude));
                    
                    // Display location information
                    frm.show_location_info(loc);
                    
                    frappe.show_alert({
                        message: __('Check-in location set to: {0}', [frm.doc.work_location]),
                        indicator: 'green'
                    });
                    
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Work Location not found.'),
                        indicator: 'red'
                    });
                }
            }
        });
    },
    
    refresh: function(frm) {
        // Add custom button to view location on external map
        if (frm.doc.current_lat && frm.doc.current_lng) {
            frm.add_custom_button(__('View on Map'), function() {
                const lat = frm.doc.current_lat;
                const lng = frm.doc.current_lng;
                const location_name = frm.doc.work_location || 'Work Location';
                
                // Open Google Maps in new tab
                window.open(`https://www.google.com/maps?q=${lat},${lng}&t=m&z=16`, '_blank');
            }, __('Location'));
            
            frm.add_custom_button(__('Get Directions'), function() {
                const lat = frm.doc.current_lat;
                const lng = frm.doc.current_lng;
                
                // Open Google Maps directions
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
            }, __('Location'));
        }
    },
    
    onload: function(frm) {
        if (frm.doc.work_location && !frm.doc.current_lat) {
            frm.trigger('work_location');
        }
    },
    
    // Show location information card
    show_location_info: function(frm, work_location_data) {
        frm.remove_location_display();
        
        const lat = parseFloat(work_location_data.latitude);
        const lng = parseFloat(work_location_data.longitude);
        const radius = work_location_data.radius || 100;
        const location_name = work_location_data.location_name || frm.doc.work_location;
        
        // Create location info card
        frm.location_display = $(`
            <div class="form-section" style="margin: 15px 0;">
                <div class="alert alert-info" style="margin: 0;">
                    <div class="row">
                        <div class="col-md-8">
                            <h5><i class="fa fa-map-marker"></i> ${location_name}</h5>
                            <p class="small" style="margin: 5px 0;">
                                <strong>Coordinates:</strong> ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
                                <strong>Check-in Radius:</strong> ${radius} meters
                            </p>
                        </div>
                        <div class="col-md-4 text-right">
                            <button class="btn btn-primary btn-sm" onclick="window.open('https://www.google.com/maps?q=${lat},${lng}&t=m&z=16', '_blank')">
                                <i class="fa fa-external-link"></i> View Map
                            </button>
                            <br><br>
                            <button class="btn btn-success btn-sm" onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}', '_blank')">
                                <i class="fa fa-location-arrow"></i> Directions
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        // Insert after work_location field
        frm.location_display.insertAfter(frm.get_field('work_location').$wrapper);
    },
    
    // Remove location display
    remove_location_display: function(frm) {
        if (frm.location_display) {
            frm.location_display.remove();
            frm.location_display = null;
        }
    },
    
    // Validate before save
    before_save: function(frm) {
        if (frm.doc.work_location && (!frm.doc.current_lat || !frm.doc.current_lng)) {
            frappe.validated = false;
            frappe.msgprint({
                title: __('Missing Location Data'),
                message: __('Please select a work location to set check-in coordinates.'),
                indicator: 'red'
            });
        }
    }
});