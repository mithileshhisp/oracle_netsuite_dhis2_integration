/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 * @NModuleScope SameAccount
 * 
 * Bank Details API - Fixed for Python Compatibility & Multiple Secondary Banks
 * - Converts all null values to empty strings for Python compatibility
 * - Allows multiple Secondary bank accounts per vendor
 * - Only restricts duplicate Primary banks (one per vendor)
 * - Supports unique bank record names via bankNameIdentifier parameter
 * - Supports inactivation via DELETE or POST with action='inactivate'
 * - Supports setting active/inactive status during creation via isActive flag
 * - FIXED: Uses boolean values for isinactive field (true/false, not 'T'/'F')
 */

define(['N/log', 'N/record', 'N/search'], function(log, record, search) {
    
    var BANK_DETAILS_RECORD = 'customrecord_2663_entity_bank_details';
    var SCRIPT_NAME = 'BankDetailsAPI';
    
    /**
     * Helper function to convert null/undefined to empty string
     * This fixes the Python error: "Only unicode objects are escapable. Got None"
     */
    function nullToEmpty(value) {
        if (value === null || value === undefined) {
            return '';
        }
        return value;
    }
    
    /**
     * Enhanced logging functions
     */
    function logInfo(step, message, data) {
        log.audit({
            title: SCRIPT_NAME + ' - ' + step,
            details: JSON.stringify({
                timestamp: new Date().toISOString(),
                message: message,
                data: data
            }, null, 2)
        });
    }
    
    function logField(fieldName, value, action) {
        log.debug({
            title: SCRIPT_NAME + ' - Field Operation',
            details: JSON.stringify({
                field: fieldName,
                action: action,
                value: typeof value === 'string' && (fieldName.includes('acct') || fieldName.includes('iban')) ? maskSensitive(value) : value,
                timestamp: new Date().toISOString()
            }, null, 2)
        });
    }
    
    function logError(step, error, context) {
        log.error({
            title: SCRIPT_NAME + ' - ERROR at ' + step,
            details: JSON.stringify({
                errorMessage: error.message,
                errorStack: error.stack,
                context: context,
                timestamp: new Date().toISOString()
            }, null, 2)
        });
    }
    
    function maskSensitive(value) {
        if (!value) return '***';
        if (value.length <= 6) return '******';
        return value.substring(0, 3) + '****' + value.substring(value.length - 3);
    }
    
    /**
     * Generate unique record name
     */
    function generateRecordName(vendorName, bankType, identifier) {
        var baseName = vendorName + ' - ' + bankType + ' Bank';
        
        if (identifier && identifier.trim() !== '') {
            return baseName + ' - ' + identifier;
        }
        
        var timestamp = new Date().getTime();
        return baseName + ' - ' + timestamp;
    }
    
    /**
     * Inactivate or reactivate a bank details record
     * FIXED: Uses boolean values for isinactive field
     */
    function setRecordActiveStatus(recordId, isActive, vendorIdForValidation) {
        var startTime = new Date();
        
        logInfo('INACTIVATE_START', 'Starting status change operation', {
            recordId: recordId,
            isActive: isActive,
            vendorIdForValidation: vendorIdForValidation
        });
        
        var bankRecord;
        try {
            bankRecord = record.load({
                type: BANK_DETAILS_RECORD,
                id: recordId
            });
        } catch (e) {
            logError('LOAD_RECORD_FAILED', e, { recordId: recordId });
            return {
                success: false,
                message: 'Bank details record not found',
                error: e.message,
                recordId: recordId
            };
        }
        
        if (vendorIdForValidation) {
            var recordVendorId = bankRecord.getValue({
                fieldId: 'custrecord_2663_parent_vendor'
            });
            
            if (recordVendorId != vendorIdForValidation) {
                logInfo('VALIDATION_FAILED', 'Record does not belong to vendor', {
                    recordId: recordId,
                    recordVendorId: recordVendorId,
                    providedVendorId: vendorIdForValidation
                });
                
                return {
                    success: false,
                    message: 'Bank details record does not belong to the specified vendor',
                    recordId: recordId,
                    vendorId: vendorIdForValidation,
                    recordVendorId: recordVendorId
                };
            }
        }
        
        // FIXED: Use boolean values, not strings
        // isActive = true -> Active -> isinactive = false
        // isActive = false -> Inactive -> isinactive = true
        var inactiveValue = !isActive;
        
        try {
            bankRecord.setValue({
                fieldId: 'isinactive',
                value: inactiveValue  // Boolean true/false
            });
            
            logField('isinactive', inactiveValue, 'SET');
            
            var savedRecordId = bankRecord.save();
            var processingTime = new Date() - startTime;
            var statusText = isActive ? 'activated' : 'inactivated';
            
            logInfo('INACTIVATE_COMPLETE', 'Record ' + statusText + ' successfully', {
                recordId: savedRecordId,
                isActive: isActive,
                processingTimeMs: processingTime
            });
            
            return {
                success: true,
                message: 'Bank details record ' + statusText + ' successfully',
                recordId: savedRecordId,
                isActive: isActive,
                processingTimeMs: processingTime
            };
            
        } catch (e) {
            logError('SAVE_STATUS_FAILED', e, {
                recordId: recordId,
                isActive: isActive,
                inactiveValue: inactiveValue
            });
            
            return {
                success: false,
                message: 'Failed to update record status: ' + e.message,
                error: e.message,
                recordId: recordId
            };
        }
    }
    
    /**
     * DELETE endpoint - Inactivate a bank details record
     */
    function doDelete(requestParams) {
        var startTime = new Date();
        var requestId = 'REQ_' + startTime.getTime() + '_' + Math.random().toString(36).substr(2, 6);
        
        logInfo('DELETE_INIT', 'DELETE API Call Started', {
            requestId: requestId,
            params: requestParams,
            timestamp: startTime.toISOString()
        });
        
        try {
            var recordId = requestParams.recordId;
            var vendorId = requestParams.vendorId;
            var isActive = requestParams.isActive !== undefined ? 
                          (requestParams.isActive === 'true' || requestParams.isActive === true) : 
                          false;
            
            if (!recordId) {
                logInfo('DELETE_VALIDATION_FAIL', 'Missing recordId', {
                    requestId: requestId,
                    receivedParams: requestParams
                });
                
                return {
                    success: false,
                    message: 'recordId is required',
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            var result = setRecordActiveStatus(recordId, isActive, vendorId);
            var totalTime = new Date() - startTime;
            
            return {
                success: result.success,
                message: result.message,
                data: {
                    recordId: nullToEmpty(result.recordId),
                    isActive: result.isActive !== undefined ? result.isActive : !isActive,
                    vendorId: nullToEmpty(vendorId)
                },
                metadata: {
                    requestId: nullToEmpty(requestId),
                    processingTimeMs: totalTime,
                    timestamp: new Date().toISOString()
                }
            };
            
        } catch (error) {
            var totalTime = new Date() - startTime;
            
            logError('DELETE Execution', error, {
                requestId: requestId,
                params: requestParams,
                totalTimeMs: totalTime
            });
            
            return {
                success: false,
                message: 'Failed to process inactivation request',
                error: nullToEmpty(error.message),
                requestId: nullToEmpty(requestId),
                timestamp: new Date().toISOString(),
                processingTimeMs: totalTime
            };
        }
    }
    
    /**
     * POST endpoint - Create bank details or handle inactivation via action parameter
     */
    function doPost(requestBody) {
        var startTime = new Date();
        var requestId = 'REQ_' + startTime.getTime() + '_' + Math.random().toString(36).substr(2, 6);
        
        logInfo('INIT', 'API Call Started', {
            requestId: requestId,
            endpoint: 'POST',
            timestamp: startTime.toISOString()
        });
        
        try {
            var data = typeof requestBody === 'string' ? JSON.parse(requestBody) : requestBody;
            
            logInfo('STEP1_COMPLETE', 'Request parsed successfully', {
                requestId: requestId,
                receivedFields: Object.keys(data),
                fieldCount: Object.keys(data).length
            });
            
            // Check if this is an inactivation request
            if (data.action === 'inactivate') {
                logInfo('ACTION_DETECTED', 'Inactivation action requested', {
                    requestId: requestId,
                    recordId: data.recordId,
                    isActive: data.isActive
                });
                
                var isActive = data.isActive !== undefined ? data.isActive : false;
                var result = setRecordActiveStatus(data.recordId, isActive, data.vendorId);
                var totalTime = new Date() - startTime;
                
                return {
                    success: result.success,
                    message: result.message,
                    data: {
                        recordId: nullToEmpty(result.recordId),
                        isActive: result.isActive !== undefined ? result.isActive : !isActive,
                        vendorId: nullToEmpty(data.vendorId)
                    },
                    metadata: {
                        requestId: nullToEmpty(requestId),
                        processingTimeMs: totalTime,
                        timestamp: new Date().toISOString()
                    }
                };
            }
            
            // ========== STEP 2: Validate Mandatory Fields (for creation) ==========
            var validationErrors = [];
            
            if (!data.vendorId) validationErrors.push('vendorId is missing');
            if (!data.bankType) validationErrors.push('bankType is missing');
            else if (data.bankType !== 'Primary' && data.bankType !== 'Secondary') 
                validationErrors.push('bankType must be "Primary" or "Secondary"');
            if (!data.fileFormatId) validationErrors.push('fileFormatId is missing');
            
            if (validationErrors.length > 0) {
                return {
                    success: false,
                    message: 'Validation failed',
                    errors: validationErrors,
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            var bankTypeValue = data.bankType === 'Primary' ? '1' : '2';
            
            // ========== STEP 3: Verify Vendor Exists ==========
            var vendorName = '';
            try {
                var vendorRecord = record.load({
                    type: 'vendor',
                    id: data.vendorId
                });
                
                vendorName = vendorRecord.getValue({ fieldId: 'entityid' }) || 
                            vendorRecord.getValue({ fieldId: 'companyname' }) || 
                            'Vendor ' + data.vendorId;
            } catch (e) {
                return {
                    success: false,
                    message: 'Vendor not found',
                    error: 'Invalid vendorId: ' + data.vendorId,
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            // ========== STEP 4: Check for Duplicates (ONLY for Primary Banks) ==========
            if (bankTypeValue === '1') {
                // FIXED: Use boolean false for Active records in search
                var duplicateSearch = search.create({
                    type: BANK_DETAILS_RECORD,
                    filters: [
                        ['custrecord_2663_parent_vendor', 'anyof', data.vendorId],
                        'AND',
                        ['custrecord_2663_entity_bank_type', 'anyof', '1'],
                        'AND',
                        ['isinactive', 'anyof', false]  // Boolean false = Active
                    ],
                    columns: ['internalid']
                });
                
                var duplicateResults = duplicateSearch.run().getRange({ start: 0, end: 1 });
                
                if (duplicateResults && duplicateResults.length > 0) {
                    return {
                        success: false,
                        message: 'Primary bank details already exist for this vendor. Only one Primary bank is allowed.',
                        existingRecordId: nullToEmpty(duplicateResults[0].id),
                        vendorName: nullToEmpty(vendorName),
                        requestId: nullToEmpty(requestId),
                        timestamp: new Date().toISOString()
                    };
                }
            }
            
            // ========== STEP 5: Create Record ==========
            var bankRecord = record.create({
                type: BANK_DETAILS_RECORD,
                isDynamic: true
            });
            
            // ========== STEP 6: Set All Fields ==========
            var fieldsSet = [];
            var fieldsSkipped = [];
            
            // Set Record Active/Inactive based on request (DEFAULT: ACTIVE)
            // FIXED: Use boolean values for isinactive
            try {
                var isActive = data.isActive !== undefined ? data.isActive : true;
                var inactiveValue = !isActive;  // Boolean: true = inactive, false = active
                var statusText = isActive ? 'Active' : 'Inactive';
                
                bankRecord.setValue({
                    fieldId: 'isinactive',
                    value: inactiveValue  // Boolean value!
                });
                fieldsSet.push({ field: 'isinactive', value: statusText });
                logField('isinactive', inactiveValue, 'SET (' + statusText + ')');
            } catch (e) {
                logError('Set Field', e, { field: 'isinactive' });
                fieldsSkipped.push({ field: 'isinactive', error: e.message });
            }
            
            // Set Record Name
            try {
                var nameIdentifier = data.bankNameIdentifier || data.uin || data.accountSuffix || null;
                var recordName = generateRecordName(vendorName, data.bankType, nameIdentifier);
                
                bankRecord.setValue({
                    fieldId: 'name',
                    value: recordName
                });
                fieldsSet.push({ field: 'name', value: recordName });
                logField('name', recordName, 'SET');
            } catch (e) {
                logError('Set Field', e, { field: 'name' });
                fieldsSkipped.push({ field: 'name', error: e.message });
            }          
            
            // Set Parent Vendor
            try {
                bankRecord.setValue({
                    fieldId: 'custrecord_2663_parent_vendor',
                    value: data.vendorId
                });
                fieldsSet.push({ field: 'custrecord_2663_parent_vendor', value: data.vendorId });
                logField('custrecord_2663_parent_vendor', data.vendorId, 'SET');
            } catch (e) {
                logError('Set Field', e, { field: 'custrecord_2663_parent_vendor', value: data.vendorId });
                fieldsSkipped.push({ field: 'custrecord_2663_parent_vendor', error: e.message });
            }
            
            // Set Bank Type
            try {
                bankRecord.setValue({
                    fieldId: 'custrecord_2663_entity_bank_type',
                    value: bankTypeValue
                });
                fieldsSet.push({ field: 'custrecord_2663_entity_bank_type', value: bankTypeValue });
                logField('custrecord_2663_entity_bank_type', bankTypeValue, 'SET');
            } catch (e) {
                logError('Set Field', e, { field: 'custrecord_2663_entity_bank_type', value: bankTypeValue });
                fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_type', error: e.message });
            }
            
            // Set File Format
            try {
                bankRecord.setValue({
                    fieldId: 'custrecord_2663_entity_file_format',
                    value: data.fileFormatId
                });
                fieldsSet.push({ field: 'custrecord_2663_entity_file_format', value: data.fileFormatId });
                logField('custrecord_2663_entity_file_format', data.fileFormatId, 'SET');
            } catch (e) {
                logError('Set Field', e, { field: 'custrecord_2663_entity_file_format', value: data.fileFormatId });
                fieldsSkipped.push({ field: 'custrecord_2663_entity_file_format', error: e.message });
            }
            
            // OPTIONAL FIELDS - Account Information
            if (data.accountNumber) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_acct_no',
                        value: data.accountNumber
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_acct_no', value: '***MASKED***' });
                    logField('custrecord_2663_entity_acct_no', data.accountNumber, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_acct_no' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_acct_no', error: e.message });
                }
            }
            
            if (data.accountName) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_acct_name',
                        value: data.accountName
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_acct_name', value: data.accountName });
                    logField('custrecord_2663_entity_acct_name', data.accountName, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_acct_name' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_acct_name', error: e.message });
                }
            }
            
            // Bank Information
            if (data.bankNumber) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bank_no',
                        value: data.bankNumber
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bank_no', value: data.bankNumber });
                    logField('custrecord_2663_entity_bank_no', data.bankNumber, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bank_no' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_no', error: e.message });
                }
            }
            
            if (data.bankName) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bank_name',
                        value: data.bankName
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bank_name', value: data.bankName });
                    logField('custrecord_2663_entity_bank_name', data.bankName, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bank_name' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_name', error: e.message });
                }
            }
            
            if (data.branchNumber) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_branch_no',
                        value: data.branchNumber
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_branch_no', value: data.branchNumber });
                    logField('custrecord_2663_entity_branch_no', data.branchNumber, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_branch_no' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_branch_no', error: e.message });
                }
            }
            
            if (data.branchName) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_branch_name',
                        value: data.branchName
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_branch_name', value: data.branchName });
                    logField('custrecord_2663_entity_branch_name', data.branchName, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_branch_name' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_branch_name', error: e.message });
                }
            }
            
            if (data.accountSuffix) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_acct_suffix',
                        value: data.accountSuffix
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_acct_suffix', value: data.accountSuffix });
                    logField('custrecord_2663_entity_acct_suffix', data.accountSuffix, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_acct_suffix' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_acct_suffix', error: e.message });
                }
            }
            
            if (data.accountType) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_acct_type',
                        value: data.accountType
                    });
                    fieldsSet.push({ field: 'custrecord_2663_acct_type', value: data.accountType });
                    logField('custrecord_2663_acct_type', data.accountType, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_acct_type' });
                    fieldsSkipped.push({ field: 'custrecord_2663_acct_type', error: e.message });
                }
            }
            
            // International Banking
            if (data.iban) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_iban',
                        value: data.iban
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_iban', value: '***MASKED***' });
                    logField('custrecord_2663_entity_iban', data.iban, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_iban' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_iban', error: e.message });
                }
            }
            
            if (data.swift) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_swift',
                        value: data.swift
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_swift', value: data.swift });
                    logField('custrecord_2663_entity_swift', data.swift, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_swift' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_swift', error: e.message });
                }
            }
            
            if (data.bic) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bic',
                        value: data.bic
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bic', value: data.bic });
                    logField('custrecord_2663_entity_bic', data.bic, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bic' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bic', error: e.message });
                }
            }
            
            // Address Information
            if (data.address1) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_address1',
                        value: data.address1
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_address1', value: data.address1 });
                    logField('custrecord_2663_entity_address1', data.address1, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_address1' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_address1', error: e.message });
                }
            }
            
            if (data.address2) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_address2',
                        value: data.address2
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_address2', value: data.address2 });
                    logField('custrecord_2663_entity_address2', data.address2, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_address2' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_address2', error: e.message });
                }
            }
            
            if (data.city) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_city',
                        value: data.city
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_city', value: data.city });
                    logField('custrecord_2663_entity_city', data.city, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_city' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_city', error: e.message });
                }
            }
            
            if (data.state) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_state',
                        value: data.state
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_state', value: data.state });
                    logField('custrecord_2663_entity_state', data.state, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_state' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_state', error: e.message });
                }
            }
            
            if (data.zip) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_zip',
                        value: data.zip
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_zip', value: data.zip });
                    logField('custrecord_2663_entity_zip', data.zip, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_zip' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_zip', error: e.message });
                }
            }
            
            if (data.country) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_country',
                        value: data.country
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_country', value: data.country });
                    logField('custrecord_2663_entity_country', data.country, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_country' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_country', error: e.message });
                }
            }
            
            // Additional Fields
            if (data.customerCode) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_customer_code',
                        value: data.customerCode
                    });
                    fieldsSet.push({ field: 'custrecord_2663_customer_code', value: data.customerCode });
                    logField('custrecord_2663_customer_code', data.customerCode, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_customer_code' });
                    fieldsSkipped.push({ field: 'custrecord_2663_customer_code', error: e.message });
                }
            }
            
            if (data.edi !== undefined) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_edi',
                        value: data.edi
                    });
                    fieldsSet.push({ field: 'custrecord_2663_edi', value: data.edi });
                    logField('custrecord_2663_edi', data.edi, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_edi' });
                    fieldsSkipped.push({ field: 'custrecord_2663_edi', error: e.message });
                }
            }
            
            if (data.babyBonus !== undefined) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_baby_bonus',
                        value: data.babyBonus
                    });
                    fieldsSet.push({ field: 'custrecord_2663_baby_bonus', value: data.babyBonus });
                    logField('custrecord_2663_baby_bonus', data.babyBonus, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_baby_bonus' });
                    fieldsSkipped.push({ field: 'custrecord_2663_baby_bonus', error: e.message });
                }
            }
            
            if (data.chargeBearer) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_chargebearer',
                        value: data.chargeBearer
                    });
                    fieldsSet.push({ field: 'custrecord_chargebearer', value: data.chargeBearer });
                    logField('custrecord_chargebearer', data.chargeBearer, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_chargebearer' });
                    fieldsSkipped.push({ field: 'custrecord_chargebearer', error: e.message });
                }
            }
            
            if (data.bankFeeCode) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bank_fee_code',
                        value: data.bankFeeCode
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bank_fee_code', value: data.bankFeeCode });
                    logField('custrecord_2663_entity_bank_fee_code', data.bankFeeCode, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bank_fee_code' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_fee_code', error: e.message });
                }
            }
            
            if (data.subsidiaryId) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_9572_subsidiary',
                        value: data.subsidiaryId
                    });
                    fieldsSet.push({ field: 'custrecord_9572_subsidiary', value: data.subsidiaryId });
                    logField('custrecord_9572_subsidiary', data.subsidiaryId, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_9572_subsidiary' });
                    fieldsSkipped.push({ field: 'custrecord_9572_subsidiary', error: e.message });
                }
            }
            
            // ========== STEP 7: Save Record ==========
            var recordId = bankRecord.save();
            
            // ========== STEP 8: Return Success Response ==========
            var totalTime = new Date() - startTime;
            
            return {
                success: true,
                message: 'Bank details created successfully',
                data: {
                    recordId: nullToEmpty(recordId),
                    vendorId: nullToEmpty(data.vendorId),
                    vendorName: nullToEmpty(vendorName),
                    bankType: nullToEmpty(data.bankType),
                    fileFormatId: nullToEmpty(data.fileFormatId),
                    isActive: data.isActive !== undefined ? data.isActive : true,
                    fieldsSet: fieldsSet.length,
                    netsuiteUrl: nullToEmpty('https://4533524-sb1.app.netsuite.com/app/common/custom/custrecord.nl?rectype=2663&id=' + recordId)
                },
                metadata: {
                    requestId: nullToEmpty(requestId),
                    processingTimeMs: totalTime,
                    timestamp: new Date().toISOString(),
                    fieldsProcessed: {
                        total: fieldsSet.length,
                        list: fieldsSet.map(function(f) { return nullToEmpty(f.field); })
                    }
                }
            };
            
        } catch (error) {
            var totalTime = new Date() - startTime;
            
            logError('Main Execution', error, {
                requestId: requestId,
                requestBody: typeof requestBody === 'string' ? requestBody.substring(0, 500) : 'Object',
                totalTimeMs: totalTime
            });
            
            return {
                success: false,
                message: 'Failed to create bank details',
                error: nullToEmpty(error.message),
                errorType: nullToEmpty(error.name),
                requestId: nullToEmpty(requestId),
                timestamp: new Date().toISOString(),
                processingTimeMs: totalTime
            };
        }
    }
    
    /**
     * GET endpoint - Retrieve bank details with null safety for Python
     */
    function doGet(requestParams) {
        var startTime = new Date();
        var requestId = 'REQ_' + startTime.getTime() + '_' + Math.random().toString(36).substr(2, 6);
        
        logInfo('GET_INIT', 'GET API Call Started', {
            requestId: requestId,
            params: requestParams,
            timestamp: startTime.toISOString()
        });
        
        try {
            var vendorId = requestParams.vendorId;
            var bankType = requestParams.bankType || 'Primary';
            var includeInactive = requestParams.includeInactive === 'true' || requestParams.includeInactive === true;
            
            if (!vendorId) {
                return {
                    success: false,
                    message: 'vendorId is required',
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            var bankTypeValue = bankType === 'Primary' ? '1' : '2';
            
            var filters = [
                ['custrecord_2663_parent_vendor', 'anyof', vendorId],
                'AND',
                ['custrecord_2663_entity_bank_type', 'anyof', bankTypeValue]
            ];
            
            // FIXED: Use boolean false for Active records
            if (!includeInactive) {
                filters.push('AND');
                filters.push(['isinactive', 'anyof', false]);  // Boolean false = Active
            }
            
            var bankSearch = search.create({
                type: BANK_DETAILS_RECORD,
                filters: filters,
                columns: [
                    'internalid',
                    'name',
                    'isinactive',
                    'custrecord_2663_entity_bank_type',
                    'custrecord_2663_entity_file_format',
                    'custrecord_2663_entity_acct_no',
                    'custrecord_2663_entity_acct_name',
                    'custrecord_2663_entity_bank_no',
                    'custrecord_2663_entity_bank_name',
                    'custrecord_2663_entity_branch_no',
                    'custrecord_2663_entity_branch_name',
                    'custrecord_2663_entity_iban',
                    'custrecord_2663_entity_swift',
                    'custrecord_2663_entity_bic',
                    'custrecord_2663_entity_address1',
                    'custrecord_2663_entity_address2',
                    'custrecord_2663_entity_city',
                    'custrecord_2663_entity_state',
                    'custrecord_2663_entity_zip',
                    'custrecord_2663_entity_country',
                    'custrecord_2663_customer_code',
                    'custrecord_2663_edi',
                    'custrecord_2663_baby_bonus',
                    'custrecord_chargebearer',
                    'custrecord_2663_entity_bank_fee_code',
                    'custrecord_9572_subsidiary'
                ]
            });
            
            var results = [];
            
            bankSearch.run().each(function(result) {
                // FIXED: Compare with boolean true
                var isInactive = result.getValue('isinactive') === true;
                var record = {
                    recordId: nullToEmpty(result.id),
                    name: nullToEmpty(result.getValue('name')),
                    isActive: !isInactive,
                    bankType: result.getValue('custrecord_2663_entity_bank_type') === '1' ? 'Primary' : 'Secondary',
                    fileFormatId: nullToEmpty(result.getValue('custrecord_2663_entity_file_format')),
                    accountNumber: nullToEmpty(result.getValue('custrecord_2663_entity_acct_no')),
                    accountName: nullToEmpty(result.getValue('custrecord_2663_entity_acct_name')),
                    bankNumber: nullToEmpty(result.getValue('custrecord_2663_entity_bank_no')),
                    bankName: nullToEmpty(result.getValue('custrecord_2663_entity_bank_name')),
                    branchNumber: nullToEmpty(result.getValue('custrecord_2663_entity_branch_no')),
                    branchName: nullToEmpty(result.getValue('custrecord_2663_entity_branch_name')),
                    iban: nullToEmpty(result.getValue('custrecord_2663_entity_iban')),
                    swift: nullToEmpty(result.getValue('custrecord_2663_entity_swift')),
                    bic: nullToEmpty(result.getValue('custrecord_2663_entity_bic')),
                    address1: nullToEmpty(result.getValue('custrecord_2663_entity_address1')),
                    address2: nullToEmpty(result.getValue('custrecord_2663_entity_address2')),
                    city: nullToEmpty(result.getValue('custrecord_2663_entity_city')),
                    state: nullToEmpty(result.getValue('custrecord_2663_entity_state')),
                    zip: nullToEmpty(result.getValue('custrecord_2663_entity_zip')),
                    country: nullToEmpty(result.getValue('custrecord_2663_entity_country')),
                    customerCode: nullToEmpty(result.getValue('custrecord_2663_customer_code')),
                    edi: nullToEmpty(result.getValue('custrecord_2663_edi')),
                    babyBonus: nullToEmpty(result.getValue('custrecord_2663_baby_bonus')),
                    chargeBearer: nullToEmpty(result.getValue('custrecord_chargebearer')),
                    bankFeeCode: nullToEmpty(result.getValue('custrecord_2663_entity_bank_fee_code')),
                    subsidiaryId: nullToEmpty(result.getValue('custrecord_9572_subsidiary'))
                };
                results.push(record);
                return true;
            });
            
            var totalTime = new Date() - startTime;
            
            return {
                success: true,
                data: {
                    vendorId: nullToEmpty(vendorId),
                    bankType: nullToEmpty(bankType),
                    records: results,
                    count: results.length,
                    includeInactive: includeInactive
                },
                metadata: {
                    requestId: nullToEmpty(requestId),
                    processingTimeMs: totalTime,
                    timestamp: new Date().toISOString()
                }
            };
            
        } catch (error) {
            var totalTime = new Date() - startTime;
            
            logError('GET Execution', error, {
                requestId: requestId,
                params: requestParams,
                totalTimeMs: totalTime
            });
            
            return {
                success: false,
                message: nullToEmpty(error.message),
                requestId: nullToEmpty(requestId),
                timestamp: new Date().toISOString(),
                processingTimeMs: totalTime
            };
        }
    }
    
    return {
        post: doPost,
        get: doGet,
        delete: doDelete
    };
});